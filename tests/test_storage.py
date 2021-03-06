import spongeblob as sb
import pytest
from azure.common import AzureMissingResourceHttpError


@pytest.fixture(scope='module')
def storage_clients(request, blob_services, lowlevel_storage_clients,
                    test_data, test_with_docker):
    test_creds = test_data['creds']
    test_providers = test_data['providers']
    clients = {provider: sb.setup_storage(provider, **test_creds[provider])
               for provider in test_providers}

    if test_with_docker:
        if 's3' in test_providers:
            clients['s3'].client = lowlevel_storage_clients['s3']
        if 'wabs' in test_providers:
            clients['wabs'].client = lowlevel_storage_clients['wabs']

    def cleanup():
        if not test_with_docker:
            try:
                for provider in test_providers:
                    clients[provider].delete_key(test_data['file1'])
                    clients[provider].delete_key(test_data['file2'])
            except AzureMissingResourceHttpError:
                pass

    request.addfinalizer(cleanup)
    return clients


@pytest.mark.xfail(raises=StopIteration)
def test_list_objects_key(test_data, test_provider, storage_clients):
    test_prefix = test_data['prefix']
    storage_client = storage_clients[test_provider]
    next(storage_client.list_object_keys(test_prefix))


def test_upload_file(test_data, test_provider, upload_file, storage_clients):
    storage_client = storage_clients[test_provider]
    test_file1 = test_data['file1']
    storage_client.upload_file(test_file1, upload_file,
                               metadata={"key1": "metadata1"})
    obj_data = next(storage_client.list_object_keys(test_file1))
    assert obj_data['key'] == test_file1
    assert obj_data['metadata'] is None


def test_uploaded_file_metadata(test_data, test_provider, upload_file,
                                storage_clients):
    test_file1 = test_data['file1']
    storage_client = storage_clients[test_provider]
    obj_data = next(storage_client.list_object_keys(test_file1, metadata=True))
    assert obj_data['metadata']['key1'] == 'metadata1'


def test_copy_from_key(test_data, test_provider, storage_clients):
    test_file1 = test_data['file1']
    test_file2 = test_data['file2']
    storage_client = storage_clients[test_provider]
    storage_client.copy_from_key(test_file1, test_file2)
    obj_data = next(storage_client.list_object_keys(test_file2))
    assert obj_data['key'] == test_file2


# following test passes but doesn't work correctly for paginators with fakes3,
# but works on s3
def test_pagination(test_data, test_provider, storage_clients):
    test_prefix = test_data['prefix']
    storage_client = storage_clients[test_provider]
    assert sum(1 for item in
               storage_client.list_object_keys(test_prefix, pagesize=1)) == 2


def test_list_object_keys_flat(test_data, test_provider, storage_clients):
    test_file1 = test_data['file1']
    test_file2 = test_data['file2']
    test_prefix = test_data['prefix']
    storage_client = storage_clients[test_provider]
    object_list = storage_client.list_object_keys_flat(test_prefix, pagesize=1,
                                                       metadata=True)
    assert isinstance(object_list, list)
    assert len(object_list) is 2

    key_list = [obj['key'] for obj in object_list]
    assert test_file1 in key_list
    assert test_file2 in key_list

    assert object_list[0]['metadata']['key1'] == 'metadata1'
    assert object_list[1]['metadata']['key1'] == 'metadata1'


def test_get_object_properties(test_data, test_provider, storage_clients):
    test_file1 = test_data['file1']
    test_file2 = test_data['file2']
    test_prefix = test_data['prefix']
    storage_client = storage_clients[test_provider]
    test_object1 = storage_client.get_object_properties(test_file1,
                                                        metadata=True)
    test_object2 = storage_client.get_object_properties(test_file2,
                                                        metadata=True)
    test_bogus_object = storage_client.get_object_properties("bogus",
                                                             metadata=True)
    test_prefix_object = storage_client.get_object_properties(test_prefix,
                                                              metadata=True)

    assert test_object1['metadata']['key1'] == 'metadata1'
    assert test_object2['metadata']['key1'] == 'metadata1'
    assert test_bogus_object is None
    assert test_prefix_object is None

@pytest.mark.xfail(raises=StopIteration)
def test_delete_key_test1(test_data, test_provider, storage_clients):
    test_file1 = test_data['file1']
    storage_client = storage_clients[test_provider]
    storage_client.delete_key(test_file1)
    next(storage_client.list_object_keys(test_file1))


def test_download_file(test_data, test_provider, download_file,
                       storage_clients):
    test_file2 = test_data['file2']
    test_filecontents = test_data['filecontents']
    storage_client = storage_clients[test_provider]
    storage_client.download_file(test_file2, download_file)
    with open(download_file, 'r') as f:
        assert f.read() == test_filecontents


@pytest.mark.xfail(raises=StopIteration)
def test_delete_key_test2(test_data, test_provider, storage_clients):
    test_file2 = test_data['file2']
    storage_client = storage_clients[test_provider]
    storage_client.delete_key(test_file2)
    next(storage_client.list_object_keys(test_file2))


@pytest.mark.xfail(raises=StopIteration)
def test_list_objects_keys_again(test_data, test_provider, storage_clients):
    test_prefix = test_data['prefix']
    storage_client = storage_clients[test_provider]
    next(storage_client.list_object_keys(test_prefix))
