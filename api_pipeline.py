import requests, json, os, datetime

def Get_Access_Token(credentials): 
    ### getting access_token ###
    '''
    credentials should be a path to file containing florence login email and password
    '''
    
    zebedee_url = 'https://publishing.ons.gov.uk/zebedee/login'
    
    with open(credentials, 'r') as json_file:
        credentials_json = json.load(json_file)
    
    email = credentials_json['email']
    password = credentials_json['password']
    login = {"email":email, "password":password}
    
    r = requests.post(zebedee_url, json=login, verify=False)
    if r.status_code == 200:
        access_token = r.text.strip('"')
        return access_token
    else:
        raise Exception('Token not created, returned a {} error'.format(r.status_code))


def Get_Recipe_Api(access_token):
    ''' returns whole recipe api '''
    
    recipe_api_url = 'https://publishing.ons.gov.uk/recipes'
    headers = {'X-Florence-Token':access_token}
    
    r = requests.get(recipe_api_url + '?limit=1000', headers=headers)
    
    if r.status_code == 200:
        recipe_dict = r.json()
        return recipe_dict
    else:
        raise Exception('Recipe API returned a {} error'.format(r.status_code))
        
        
def Check_Recipe_Exists(access_token, dataset_id):
    '''
    Checks to make sure a recipe exists for dataset_id
    Returns nothing if recipe exists, an error if not
    Uses Get_Recipe_Api()
    '''
    recipe_dict = Get_Recipe_Api(access_token)
    # create a list of all existing dataset ids
    dataset_id_list = []
    for item in recipe_dict['items']:
        dataset_id_list.append(item['output_instances'][0]['dataset_id'])
    if dataset_id not in dataset_id_list:
        raise Exception('Recipe does not exist for {}'.format(dataset_id))
    

def Get_Recipe(access_token, dataset_id):
    ''' 
    Returns recipe for specific dataset 
    Uses Get_Recipe_Api()
    dataset_id is the dataset_id from the recipe
    '''
    Check_Recipe_Exists(access_token, dataset_id)
    recipe_dict = Get_Recipe_Api(access_token)
    # iterate through recipe api to find correct dataset_id
    for item in recipe_dict['items']:
        if dataset_id == item['output_instances'][0]['dataset_id']:
            return item


def Get_Recipe_Info(access_token, dataset_id):
    ''' 
    Returns useful recipe information for specific dataset 
    Uses Get_Recipe()
    '''
    recipe_dict = Get_Recipe(access_token, dataset_id)
    recipe_info_dict = {}
    recipe_info_dict['dataset_id'] = dataset_id
    recipe_info_dict['recipe_alias'] = recipe_dict['files'][0]['description']
    recipe_info_dict['recipe_id'] = recipe_dict['id']
    return recipe_info_dict
    
    
def Get_Recipe_Info_From_Recipe_Id(access_token, recipe_id):
    '''
    Returns useful recipe information for specific dataset
    Uses recipe_id to get recipe information
    '''
    
    recipe_api_url = 'https://publishing.ons.gov.uk/recipes'
    single_recipe_url = recipe_api_url + '/' + recipe_id 
    
    headers = {'X-Florence-Token':access_token}
    
    r = requests.get(single_recipe_url, headers=headers)
    if r.status_code == 200:
        single_recipe_dict = r.json()
        return single_recipe_dict
    else:
        raise Exception('Get_Recipe_Info_From_Recipe_Id returned a {} error'.format(r.status_code))


def Update_Recipe(access_token, dataset_id, updated_recipe_dict):
    '''
    Updates a specific recipe 
    Updates top level of recipe dict -> alias, format, id
    Pass a dict with required changes
    ie
    new_recipe = {}
    new_recipe['alias'] = 'A new title'
    Can be used to update output_instances - my_dict['output_instances'] = [{}]
    '''
    
    recipe_dict = Get_Recipe_Info(access_token, dataset_id)
    recipe_id = recipe_dict['recipe_id']
    
    recipe_api_url = 'https://publishing.ons.gov.uk/recipes'
    single_recipe_url = recipe_api_url + '/' + recipe_id
    
    headers = {'X-Florence-Token':access_token}
    
    r = requests.put(single_recipe_url, headers=headers, json=updated_recipe_dict)
    
    if r.status_code == 200:
        print('Recipe updated successfully!')
        new_recipe_dict = Get_Recipe(access_token, dataset_id)
        del new_recipe_dict['files']
        del new_recipe_dict['output_instances']
        print(new_recipe_dict)
    else:
        print('Recipe not updated, returned a {} error'.format(r.status_code))


def Update_Recipe_Editions(access_token, dataset_id, list_of_editions):
    '''
    Updates the editions for a specific recipe 
    Pass a list of new editions
    '''
    if type(list_of_editions) != list:
        raise Exception('list_of_editions needs to be a list, not a {}'.format(type(list_of_editions)))
    
    recipe_dict = Get_Recipe_Info(access_token, dataset_id)
    recipe_id = recipe_dict['recipe_id']
    
    recipe_api_url = 'https://publishing.ons.gov.uk/recipes'
    single_recipe_url = recipe_api_url + '/' + recipe_id + '/instances/' + dataset_id
    
    headers = {'X-Florence-Token':access_token}
    
    new_editions_dict = {}
    new_editions_dict['editions'] = list_of_editions
    
    r = requests.put(single_recipe_url, headers=headers, json=new_editions_dict)
    
    if r.status_code == 200:
        print('Editions updated successfully!')
        new_recipe_dict = Get_Recipe(access_token, dataset_id)
        print(new_recipe_dict['output_instances'][0]['editions'])
    else:
        print('Editions not updated, returned a {} error'.format(r.status_code))
    

def Update_Recipe_Codelists(access_token, dataset_id, codelist_changes_dict, codelist_id):
    '''
    Updates a single codelist for a single recipe 
    Pass a dict with required changes
    codelist_info = {
            'id':'',
            'name':'',
            'is_hierarchy':'',
            'href':''
            }
    '''
    recipe_dict = Get_Recipe_Info(access_token, dataset_id)
    recipe_id = recipe_dict['recipe_id']
    
    recipe_api_url = 'https://publishing.ons.gov.uk/recipes'
    single_recipe_url = recipe_api_url + '/' + recipe_id + '/instances/' + dataset_id + '/code-lists/' + codelist_id
    
    headers = {'X-Florence-Token':access_token}
    
    r = requests.put(single_recipe_url, headers=headers, json=codelist_changes_dict)
    
    if r.status_code == 200:
        print('Codelist updated successfully!')
        new_recipe_dict = Get_Recipe(access_token, dataset_id)
        print(new_recipe_dict['output_instances'][0]['code_lists'])
    else:
        print('Codelist not updated, returned a {} error'.format(r.status_code))
    
def Post_New_Recipe_In_Api(access_token, recipe_dict):
    '''
    Creates a new recipe in recipe api
    '''
    Check_Recipe_Dict(recipe_dict)
    
    recipe_api_url = 'https://publishing.ons.gov.uk/recipes'
    
    headers = {'X-Florence-Token':access_token}
    
    r = requests.post(recipe_api_url, headers=headers, json=recipe_dict)
    
    dataset_id = recipe_dict['output_instances'][0]['dataset_id']
    
    if r.status_code == 200:
        print('Recipe created successfully!')
        new_recipe_dict = Get_Recipe(access_token, dataset_id)
        print('New recipe info pulled from api')
        print(new_recipe_dict)
    else:
        print('Recipe not created successfully, returned a {} error'.format(r.status_code))
    
def Check_Recipe_Dict(recipe_dict):
    '''
    Checks the format of a new recipe_dict
    '''
    assert recipe_dict['alias'] != 'Alias of dataset', 'alias needs updating'
    assert type(recipe_dict['files']) == list
    assert recipe_dict['files'][0]['description'] != 'DescriptionOfDataset', 'description needs updating'
    assert recipe_dict['id'] != 'unique-string-of-characters', 'id needs updating'
    assert type(recipe_dict['output_instances']) == list
    assert recipe_dict['output_instances'][0]['dataset_id'] != 'id-of-dataset', 'dataset_id needs updating'
    assert type(recipe_dict['output_instances'][0]['editions']) == list
    assert recipe_dict['output_instances'][0]['editions'] != [], 'recipe needs at least one edition'
    assert recipe_dict['output_instances'][0]['title'] != 'Title of dataset', 'title needs updating'
    assert type(recipe_dict['output_instances'][0]['code_lists']) == list
    assert len(recipe_dict['output_instances'][0]['code_lists']) != 0, 'code lists need updating'
    print('recipe_dict passes format test')
    

def Create_Recipe_Dict():
    '''
    returns an "empty" dict of the correct format for a new recipe
    '''
    recipe_dict = {}
    recipe_dict['alias'] = 'Alias of dataset'
    recipe_dict['files'] = [{'description':'DescriptionOfDataset'}]
    recipe_dict['format'] = 'v4'
    recipe_dict['id'] = 'unique-string-of-characters'
    recipe_dict['output_instances'] = [{'code_lists':[],
                                        'dataset_id':'id-of-dataset',
                                        'editions':[],
                                        'title':'Title of dataset'
                                        }
                                ]
    return recipe_dict


def Update_Details_Of_Recipe_Dict(recipe_dict):
    '''
    Auto fills the recipe_dict
    '''
    print('alias -> Alias of dataset')
    recipe_dict['alias'] = input('alias: ')
    
    print('description -> DescriptionOfDataset')
    recipe_dict['files'][0]['description'] = input('description : ')
    
    print('id -> unique-string-of-characters')
    recipe_dict['id'] = input('id: ')
    
    print('dataset_id -> id-of-dataset')
    recipe_dict['output_instances'][0]['dataset_id'] = input('dataset_id: ')
    
    print('title -> Title of dataset')
    recipe_dict['output_instances'][0]['title'] = input('title: ')
    
    number_of_editions = int(input('Number of editions: '))
    editions = []
    for i in range(number_of_editions):
        edition = input('Edition {}: '.format(i+1))
        editions.append(edition)
    recipe_dict['output_instances'][0]['editions'] = editions
    
    number_of_codelists = int(input('Number of code lists: '))
    code_list_dict = {}
    for i in range(number_of_codelists):
        code_id = input('code list id {}: '.format(i+1))
        code_label = input('code list label {}: '.format(i+1))
        has_hierarchy = input('does {} have hierarchy [y/n]: '.format(code_id))
        code_list_dict.update({code_id:code_label.lower()})
        if has_hierarchy.lower() == 'y':
            code_list_dict.update({code_id + '_hierarchy':True})
        else:
            code_list_dict.update({code_id + '_hierarchy':False})
    recipe_dict = Update_Codelist_Dict_For_Recipe(recipe_dict, code_list_dict)
    
    return recipe_dict
    

def Update_Codelist_Dict_For_Recipe(recipe_dict, code_lists_id_label_dict):
    '''
    Creates a list of code lists to be added to the recipe_dict
    required format: {admin-geography:geography, calendar-years:time}
    if code list has a hierarchy add in code_list_id_hierarchy:True
    '''
    assert type(code_lists_id_label_dict) == dict, 'code_lists_id_label_dict needs to be a dict'
    recipe_codelists = []
    for key in code_lists_id_label_dict.keys():
        if key.endswith('_hierarchy'):
            continue
        loop_dict = {}
        loop_dict['href'] = 'http://localhost:22400/code-lists/' + key
        loop_dict['id'] = key
        loop_dict['name'] = code_lists_id_label_dict[key]
        if key + '_hierarchy' in code_lists_id_label_dict.keys():
            loop_dict['is_hierarchy'] = code_lists_id_label_dict[key + '_hierarchy']
        
        recipe_codelists.append(loop_dict)
    recipe_dict['output_instances'][0]['code_lists'] = recipe_codelists
    
    return recipe_dict


def Get_Dataset_Instances_Api(access_token):
    ''' 
    Returns /dataset/instances API 
    '''
    dataset_instances_api_url = 'https://publishing.ons.gov.uk/dataset/instances'
    headers = {'X-Florence-Token':access_token}
    
    r = requests.get(dataset_instances_api_url + '?limit=1000', headers=headers)
    if r.status_code == 200:
        whole_dict = r.json()
        total_count = whole_dict['total_count']
        if total_count <= 1000:
            dataset_instances_dict = r.json()['items']
        elif total_count > 1000:
            number_of_iterations = round(total_count / 1000) + 1
            offset = 0
            dataset_instances_dict = []
            for i in range(number_of_iterations):
                new_url = dataset_instances_api_url + '?limit=1000&offset={}'.format(offset)
                new_dict = requests.get(new_url, headers=headers).json()
                for item in new_dict['items']:
                    dataset_instances_dict.append(item)
                offset += 1000
        return dataset_instances_dict
    else:
        raise Exception('/dataset/instances API returned a {} error'.format(r.status_code))


def Get_Latest_Dataset_Instances(access_token):
    '''
    May have a caching issue here
    Returns latest upload id
    Uses Get_Dataset_Instances_Api()
    '''
    dataset_instances_dict = Get_Dataset_Instances_Api(access_token)
    latest_id = dataset_instances_dict[0]['id']
    return latest_id


def Get_Dataset_Instance_Info(access_token, instance_id):
    '''
    Return specific dataset instance info
    '''
    dataset_instances_url = 'https://publishing.ons.gov.uk/dataset/instances/' + instance_id
    headers = {'X-Florence-Token':access_token}
    
    r = requests.get(dataset_instances_url, headers=headers)
    if r.status_code == 200:
        dataset_instances_dict = r.json()
        return dataset_instances_dict
    else:
        raise Exception('/dataset/instances/{} API returned a {} error'.format(instance_id, r.status_code))
    

def Get_Dataset_Jobs_Api(access_token):
    '''
    Returns dataset/jobs API
    '''

    dataset_jobs_api_url = 'https://publishing.ons.gov.uk/dataset/jobs'
    headers = {'X-Florence-Token':access_token}
    
    r = requests.get(dataset_jobs_api_url + '?limit=1000', headers=headers)
    if r.status_code == 200:
        whole_dict = r.json()
        total_count = whole_dict['total_count']
        if total_count <= 1000:
            dataset_jobs_dict = whole_dict['items']
        elif total_count > 1000:
            number_of_iterations = round(total_count / 1000) + 1
            offset = 0
            dataset_jobs_dict = []
            for i in range(number_of_iterations):
                new_url = dataset_jobs_api_url + '?limit=1000&offset={}'.format(offset)
                new_dict = requests.get(new_url, headers=headers).json()
                for item in new_dict['items']:
                    dataset_jobs_dict.append(item)
                offset += 1000
        return dataset_jobs_dict
    else:
        raise Exception('/dataset/jobs API returned a {} error'.format(r.status_code))
        
        
def Get_Latest_Job_Info(access_token):
    '''
    Returns latest job id and recipe id and instance id
    Uses Get_Dataset_Jobs_Api()
    '''
    dataset_jobs_dict = Get_Dataset_Jobs_Api(access_token)
    latest_id = dataset_jobs_dict[-1]['id']
    recipe_id = dataset_jobs_dict[-1]['recipe'] # to be used as a quick check
    instance_id = dataset_jobs_dict[-1]['links']['instances'][0]['id']
    return latest_id, recipe_id, instance_id


def Post_New_Job(access_token, dataset_id, s3_url):
    '''
    Creates a new job in the /dataset/jobs API
    Job is created in state 'created'
    Uses Get_Recipe_Info() to get information
    '''
    dataset_dict = Get_Recipe_Info(access_token, dataset_id)
    
    dataset_jobs_api_url = 'https://publishing.ons.gov.uk/dataset/jobs'
    headers = {'X-Florence-Token':access_token}
    
    new_job_json = {
        'recipe':dataset_dict['recipe_id'],
        'state':'created',
        'links':{},
        'files':[
            {
        'alias_name':dataset_dict['recipe_alias'],
        'url':s3_url
            }   
        ]
    }
        
    r = requests.post(dataset_jobs_api_url, headers=headers, json=new_job_json)
    if r.status_code == 201:
        print('Job created succefully')
    else:
        raise Exception('Job not created, return a {} error'.format(r.status_code))
        
    # return job ID
    job_id, job_recipe_id, job_instance_id = Get_Latest_Job_Info(access_token)
    
    # quick check to make sure newest job id is the correct one
    if job_recipe_id != dataset_dict['recipe_id']:
        print('New job recipe ID ({}) does not match recipe ID used to create new job ({})'.format(job_recipe_id, dataset_dict['recipe_id']))
    else:
        print('job_id -', job_id)
        print('dataset_instance_id -', job_instance_id)
        return job_id, job_instance_id


def Add_File_To_Existing_Job(access_token, dataset_id, job_id, s3_url):
    '''
    Adds file to a job
    Only needed if file wasnt originally attached to new job - ie files = []
    '''

    dataset_dict = Get_Recipe_Info(access_token, dataset_id)
    
    attaching_file_to_job_url = 'https://publishing.ons.gov.uk/dataset/jobs/' + job_id + '/files'
    headers = {'X-Florence-Token':access_token}
    
    added_file_json = {
            'alias_name':dataset_dict['recipe_alias'],
            'url':s3_url
            }

    r = requests.put(attaching_file_to_job_url, headers=headers, json=added_file_json)
    if r.status_code == 200:
        print('File added successfully')
    else:
        print('Error code {} from Add_File_To_Existing_Job'.format(r.status_code))


def Update_State_Of_Job(access_token, job_id):
    '''
    Updates state of job from created to submitted
    once submitted import process will begin
    '''

    updating_state_of_job_url = 'https://publishing.ons.gov.uk/dataset/jobs/' + job_id
    headers = {'X-Florence-Token':access_token}

    updating_state_of_job_json = {}
    updating_state_of_job_json['state'] = 'submitted'
    
    # make sure file is in the job before continuing
    job_id_dict = Get_Job_Info(access_token, job_id)
    
    if len(job_id_dict['files']) != 0:
        r = requests.put(updating_state_of_job_url, headers=headers, json=updating_state_of_job_json)
        if r.status_code == 200:
            print('State updated successfully')
        else:
            print('State not updated, return error code {}'.format(r.status_code))
    else:
        raise Exception('Job does not have a v4 file!')
    

def Get_Job_Info(access_token, job_id):
    '''
    Return job info
    '''
    dataset_jobs_id_url = 'https://publishing.ons.gov.uk/dataset/jobs/' + job_id
    headers = {'X-Florence-Token':access_token}
    
    r = requests.get(dataset_jobs_id_url, headers=headers)
    if r.status_code == 200:
        job_info_dict = r.json()
        return job_info_dict
    else:
        raise Exception('/dataset/jobs/{} returned error {}'.format(job_id, r.status_code))


def Upload_Data_To_Florence(credentials, dataset_id, v4):
    '''Uploads v4 into Florence'''
    # get access_token
    access_token = Get_Access_Token(credentials)
    
    #quick check to make sure recipe exists in API
    Check_Recipe_Exists(access_token, dataset_id)
    
    # upload v4 into s3 bucket
    s3_url = Post_V4_To_S3(access_token, v4)
    
    # create new job
    job_id, instance_id = Post_New_Job(access_token, dataset_id, s3_url)
    
    # update state of job
    Update_State_Of_Job(access_token, job_id)
    
    return instance_id


def Post_V4_To_S3(access_token, v4):
    '''
    Uploading a v4 to the s3 bucket
    v4 is full file path
    '''
    # properties that do not change for the upload
    csv_total_size = str(os.path.getsize(v4)) # size of the whole csv
    timestamp = datetime.datetime.now() # to be ued as unique resumableIdentifier
    timestamp = datetime.datetime.strftime(timestamp, '%d%m%y%H%M%S')
    file_name = v4.split("/")[-1]
    
    upload_url = 'https://publishing.ons.gov.uk/upload'
    headers = {'X-Florence-Token':access_token}
    
    # chunk up the data
    temp_files = Create_Temp_Chunks(v4) # list of temporary files
    total_number_of_chunks = len(temp_files)
    chunk_number = 1 # starting chunk number
    
    # uploading each chunk
    for chunk_file in temp_files:
        csv_size = str(os.path.getsize(chunk_file)) # Size of the chunk

        with open(chunk_file, 'rb') as f:
            files = {'file': f} # Inlcude the opened file in the request
            
            # Params that are added to the request
            params = {
                    "resumableType": "text/csv",
                    "resumableChunkNumber": chunk_number,
                    "resumableCurrentChunkSize": csv_size,
                    "resumableTotalSize": csv_total_size,
                    "resumableChunkSize": csv_size,
                    "resumableIdentifier": timestamp + '-' + file_name.replace('.', ''),
                    "resumableFilename": file_name,
                    "resumableRelativePath": ".",
                    "resumableTotalChunks": total_number_of_chunks
            }
            
            # making the POST request
            r = requests.post(upload_url, headers=headers, params=params, files=files)
            if r.status_code != 200:  
                raise Exception('{} returned error {}'.format(upload_url, r.status_code))
                
            chunk_number += 1 # moving onto next chunk number
        
    s3_url = 'https://s3-eu-west-1.amazonaws.com/ons-dp-production-publishing-uploaded-datasets/{}'.format(params['resumableIdentifier'])
    
    # delete temp files
    Delete_Temp_Chunks(temp_files)
    
    return s3_url
     

def Create_Temp_Chunks(v4):
    '''
    Chunks up the data into text files
    returns number of chunks
    chunks created in same directory as v4
    Will be deleted after upload
    '''
    chunk_size = 5 * 1024 * 1024
    file_number = 1
    location = '/'.join(v4.split('/')[:-1]) + '/'
    temp_files = []
    with open(v4, 'rb') as f:
        chunk = f.read(chunk_size)
        while chunk:
            file_name = location + 'temp-file-part-' + str(file_number)
            with open(file_name, 'wb') as chunk_file:
                chunk_file.write(chunk)
                temp_files.append(file_name)
            file_number += 1
            chunk = f.read(chunk_size)
    return temp_files 


def Delete_Temp_Chunks(temporary_files):
    '''
    Deletes the temporary chunks that were uploaded
    '''
    for file in temporary_files:
        os.remove(file)
    

def Get_State_Of_Instance(access_token, instance_id):
    '''
    Checks state of an instance
    Returns job_state
    '''
    instance_id_url = 'https://publishing.ons.gov.uk/dataset/instances/' + instance_id
    headers = {'X-Florence-Token':access_token}
    
    r = requests.get(instance_id_url, headers=headers)
    if r.status_code != 200:
        raise Exception('{} raised a {} error'.format(instance_id_url, r.status_code))
        
    dataset_instance_dict = r.json()
    job_state = dataset_instance_dict['state']
    
    if job_state == 'created':
        print('State of instance is "{}", import process has not been triggered'.format(job_state))
        
    elif job_state == 'submitted':
        total_inserted_observations = dataset_instance_dict['import_tasks']['import_observations']['total_inserted_observations']
        try:
            total_observations = dataset_instance_dict['total_observations']
        except:
            error_message = dataset_instance_dict['events'][0]['message']
            print('Job is submitted but total_observations could not be determined')
            print('An error has occured')
            raise Exception(error_message)
        print('Import process is running')
        print('{} out of {} observations have been imported'.format(total_inserted_observations, total_observations))
    
    elif job_state == 'completed':
        print('Import complete!')
        
    else:
        print('Instance has state - "{}"'.format(job_state))
        
    return job_state


def Update_Metadata(access_token, dataset_id, metadata_dict):
    '''
    Used to update all metadata except dimensional data and usage notes
    Updates using /dataset/datasets/{id}
    Can be used before or after data is in collection
    This metadata is saved in CMD
    Not all fields are required - only ones that need changing

    metadata is a dict with format (possible others)
    {
    collection_id : '' (may not be needed)
    contact : [{email : '', name : '', telephone : ''}] 
    description : '' (Summary section in florence)
    next_release : ''
    release_frequency : ''
    title : '' (Title section in florence)
    unit_of_measure : ''
    keywords : []
    license : ''
    national_statistic : True
    
    # some not to change
    id, links, qmi, state
    }
    
    '''
    metadata = metadata_dict['metadata']
    
    assert type(metadata) == dict, 'metadata must be a dict'
    
    dataset_url = 'https://publishing.ons.gov.uk/dataset/datasets/' + dataset_id
    headers = {'X-Florence-Token':access_token}
    
    r = requests.put(dataset_url, headers=headers, json=metadata)
    if r.status_code != 200:
        print('Metadata not updated, returned a {} error'.format(r.status_code))
    else:
        print('Metadata updated')
    

def Update_Dimensions(access_token, dataset_id, instance_id, metadata_dict):
    '''
    Used to update dimension labels and add descriptions
    Updates using /datasets/instances/{id}/dimensions/{name}
    {name} is dimension label used in the recipe ie lower case no space
    
    dimension_dict has format = {
    dimension1_name = {label:'', description:''},
    dimension2_name = {label:'', description:''},
    etc
    }
    '''
    dimension_dict = metadata_dict['dimension_data']
    assert type(dimension_dict) == dict, 'dimension_dict must be a dict'
    
    instance_url = 'https://publishing.ons.gov.uk/dataset/instances/' + instance_id
    headers = {'X-Florence-Token':access_token}
    
    for dimension in dimension_dict.keys():
        new_dimension_info = {}
        for key in dimension_dict[dimension].keys():
            new_dimension_info[key] = dimension_dict[dimension][key]
          
        # making the request for each dimension separately
        dimension_url = instance_url + '/dimensions/' + dimension
        r = requests.put(dimension_url, headers=headers, json=new_dimension_info)
        
        if r.status_code != 200:
            print('Dimension info not updated for {}, returned a {} error'.format(dimension, r.status_code))
        else:
            print('Dimension updated - {}'.format(dimension))
    
    
def Update_Usage_Notes(access_token, dataset_id, version_number, metadata_dict, edition):
    '''
    Adds usage notes to a version - only unpublished
    /datasets/{id}/editions/{edition}/versions/{version}
    usage_notes is a list of dict(s)
    
    Can do multiple at once and upload will replace any existing ones
    
    usage_notes has format = [{
            note:'', title:''
            },{
            note:'', title:''
            },
    etc
    ]
    
    does not need note and title
    '''        
    if 'usage_notes' not in metadata_dict.keys():
        return 'No usage notes to add'
    
    usage_notes = metadata_dict['usage_notes']
        
    assert type(usage_notes) == list, 'usage notes must be in a list'
    for item in usage_notes:
        for key in item.keys():
            assert key in ('note', 'title'), 'usage note can only have a note and/or a title'
        
    usage_notes_to_add = {}
    usage_notes_to_add['usage_notes'] = usage_notes
    
    version_url = 'https://publishing.ons.gov.uk/dataset/datasets/{}/editions/{}/versions/{}'.format(dataset_id, edition, version_number)
    headers = {'X-Florence-Token':access_token}
    
    r = requests.put(version_url, headers=headers, json=usage_notes_to_add)
    if r.status_code == 200:
        print('Usage notes added')
    else:
        print('Usage notes not added, returned a {} error'.format(r.status_code))
     
    
def Get_Version_number(access_token, dataset_id, instance_id):
    '''
    Gets version number of instance ready to be published from /datasets/instances{instance_id}
    Only when dataset is in a collection or edition-confirmed state
    Used to find the right version for usage notes or to add version to collection
    Returns version number as string
    '''   
    
    instance_url = 'https://publishing.ons.gov.uk/dataset/instances/' + instance_id
    headers = {'X-Florence-Token':access_token}
    
    r = requests.get(instance_url, headers=headers)
    if r.status_code != 200:
        raise Exception('/datasets/{}/instances/{} returned a {} error'.format(dataset_id, instance_id, r.status_code))
        
    instance_dict = r.json()
    version_number = instance_dict['version']
    
    # check to make sure is the right dataset
    assert instance_dict['links']['dataset']['id'] == dataset_id, '{} does not match {}'.format(instance_dict['links']['dataset']['id'], dataset_id)
    
    # check to make sure version number is a number
    assert version_number == int(version_number), 'Version number should be a number - {}'.format(version_number)
    
    return str(version_number)


def Read_CSVW(metadata_file):
    '''
    Reads in csw-w metadata file
    Returns the metadata in format usable by CMD APIs
    as a dict with 3 keys? - metadata, dimension data, usage notes
    '''
    f = open(metadata_file)
    csv_w = json.load(f)
    metadata_dict = {} # dict to be used for CMD APIs
    
    """
    Cant find a next release date - probably not needed for census though
    Also missing - keywords, national statistic
    """
    
    # split into 3
    metadata_dict['metadata'] = {}
    metadata_dict['dimension_data'] = {}
    metadata_dict['usage_notes'] = {}
    
    ### Using if statements but maybe a better way ###
    if 'dct:title' in csv_w.keys():
        metadata_dict['metadata']['title'] = csv_w['dct:title']
        
    if 'dct:description' in csv_w.keys():
        metadata_dict['metadata']['description'] = csv_w['dct:description']
      
    # release date - useful if can add data to a collection
    '''
    if 'dct:issued' in csv_w.keys():
        metadata_dict['metadata']['next_release'] = csv_w['dct:issued']
    '''
    
    if 'dct:nextRelease' in csv_w.keys():
        metadata_dict['metadata']['next_release'] = csv_w['dct:nextRelease']

    # TODO - more than one contact?
    if 'dcat:contactPoint' in csv_w.keys():
        metadata_dict['metadata']['contacts'] = [{}]
        if 'vcard:fn' in csv_w['dcat:contactPoint'][0].keys():
            metadata_dict['metadata']['contacts'][0]['name'] = csv_w['dcat:contactPoint'][0]['vcard:fn']
        if 'vcard:tel' in csv_w['dcat:contactPoint'][0].keys():
            metadata_dict['metadata']['contacts'][0]['telephone'] = csv_w['dcat:contactPoint'][0]['vcard:tel']
        if 'vcard:email' in csv_w['dcat:contactPoint'][0].keys():
            metadata_dict['metadata']['contacts'][0]['email'] = csv_w['dcat:contactPoint'][0]['vcard:email']

    if 'dct:accrualPeriodicity' in csv_w.keys():
        metadata_dict['metadata']['release_frequency'] = csv_w['dct:accrualPeriodicity']

    if 'tableSchema' in csv_w.keys():
        dimension_metadata = csv_w['tableSchema']['columns']
        metadata_dict['dimension_data'] = Dimension_Metadata_From_CSVW(dimension_metadata)
        metadata_dict['metadata']['unit_of_measure'] = Get_Unit_Of_Measure(dimension_metadata)
    
    if 'notes' in csv_w.keys():
        metadata_dict['usage_notes'] = Usage_Notes_From_CSVW(csv_w['notes'])
        
    return metadata_dict
    

def Dimension_Metadata_From_CSVW(dimension_metadata):
    '''
    Converts dimension metadata from csv-w to usable format for CMD APIs
    Takes in csv_w['tableSchema']['columns'] - is a list
    Returns a dict of dicts
    '''
    assert type(dimension_metadata) == list, 'dimension_metadata should be a list'
    
    # first item in list should be observations
    # quick check
    assert dimension_metadata[0]['titles'].lower().startswith('v4_'), 'dimension_metadata[0] is not the obs column'

    # number of data marking columns
    number_of_data_markings = int(dimension_metadata[0]['titles'].split('_')[-1])
    
    wanted_dimension_metadata = dimension_metadata[2+number_of_data_markings::2]
    dimension_metadata_for_cmd = {}
    
    for item in wanted_dimension_metadata:
        name = item['titles']
        label = item['name']
        description = item['description']
        dimension_metadata_for_cmd[name] = {'label':label, 'description':description}
        
    return dimension_metadata_for_cmd
    

def Get_Unit_Of_Measure(dimension_metadata):
    '''
    Pulls unit_of_measure from dimension metadata
    '''
    
    assert type(dimension_metadata) == list, 'dimension_metadata should be a list'
    
    # first item in list should be observations
    # quick check
    assert dimension_metadata[0]['titles'].lower().startswith('v4_'), 'dimension_metadata[0] is not the obs column'
    if 'name' in dimension_metadata[0].keys():
        unit_of_measure = dimension_metadata[0]['name']
    else:
        unit_of_measure = ''
    
    return unit_of_measure


def Usage_Notes_From_CSVW(usage_notes):
    '''
    Pulls usage notes from csv-w to usable format for CMD APIs
    Takes in csv_w['notes'] - is a list
    Creates a list of dicts
    '''
    assert type(usage_notes) == list, 'usage_notes should be a list'
    
    usage_notes_list = []
    for item in usage_notes:
        single_usage_note = {}
        single_usage_note['title'] = item['type']
        single_usage_note['note'] = item['body']
        usage_notes_list.append(single_usage_note)
        
    return usage_notes_list



def Upload_Metadata_To_Cmd(credentials, dataset_id, metadata_file, instance_id, edition):
    '''
    Uploads metadata into CMD
    Data should already be in a collection
    '''
        
    # Get access token
    access_token = Get_Access_Token(credentials)
    
    # Reading in csv-w and formatting for the CMD API functions
    metadata_dict = Read_CSVW(metadata_file)
    
    # Updating general metadata
    Update_Metadata(access_token, dataset_id, metadata_dict)
    
    # Updating dimension metadata
    Update_Dimensions(access_token, dataset_id, instance_id, metadata_dict)
    
    # Get version number of instance -> has to be in collection
    version_number = Get_Version_number(access_token, dataset_id, instance_id)
    
    # Update_Usage_Notes
    Update_Usage_Notes(access_token, dataset_id, version_number, metadata_dict, edition)
    

    
    

def Create_Collection(access_token, collection_name):
    '''
    Creates a collection with called 'collection name'
    Works but returns a 500?? 
    '''
    collection_url = 'https://publishing.ons.gov.uk/zebedee/collection'
    headers = {'X-Florence-Token':access_token}
    
    requests.post(collection_url, headers=headers, json={'name':collection_name})
    
def Check_Collection_Exists(access_token, collection_name):
    '''
    Checks to make sure a collection was created
    TODO - check to make sure collection is empty
    '''
    collection_name_for_url = collection_name.replace(' ', '').lower()
    
    collection_url = 'https://publishing.ons.gov.uk/zebedee/collection'
    headers = {'X-Florence-Token':access_token}
    
    r = requests.get(collection_url + '/' + collection_name_for_url, headers=headers)
    if r.status_code != 200:
        raise Exception('Collection "{}" not created - returned a {} error'.format(collection_name, r.status_code))
    
def Get_Collection_Id(access_token, collection_name):
    '''
    Returns the collection id from a given collection name
    '''
    collection_name_for_url = collection_name.replace(' ', '').lower() # used in request
    
    collection_url = 'https://publishing.ons.gov.uk/zebedee/collection'
    headers = {'X-Florence-Token':access_token}
    
    r = requests.get(collection_url + '/' + collection_name_for_url, headers=headers)
    if r.status_code == 200:
        collection_dict = r.json()
        collection_id = collection_dict['id']
        return collection_id
    else:
        raise Exception('Collection "{}" not found - returned a {} error'.format(collection_name, r.status_code))

def Add_Dataset_To_Collection(access_token, collection_id, dataset_id):
    '''
    Adds dataset landing page to collection
    '''
    url = 'https://publishing.ons.gov.uk/zebedee/collections/{}/datasets/{}'.format(collection_id, dataset_id)
    headers = {'X-Florence-Token':access_token}
    
    r = requests.put(url, headers=headers, json={"state": "Complete"})
    if r.status_code == 200:
        print('{} - Dataset landing page added to collection'.format(dataset_id))
    else:
        raise Exception('{} - Dataset landing page not added to collection - returned a {} error'.format(dataset_id, r.status_code))

def Add_Dataset_Version_To_Collection(access_token, collection_id, dataset_id, edition, version_number):
    '''
    Adds dataset version to collection
    '''
    url = 'https://publishing.ons.gov.uk/zebedee/collections/{}/datasets/{}/editions/{}/versions/{}'.format(collection_id, dataset_id, edition, version_number)
    headers = {'X-Florence-Token':access_token}
    
    r = requests.put(url, headers=headers, json={"state": "Complete"})
    if r.status_code == 200:
        print('{} - Dataset version "{}" added to collection'.format(dataset_id, version_number))
    else:
        raise Exception('{} - Dataset version "{}" not added to collection - returned a {} error'.format(dataset_id, version_number, r.status_code))


def Create_New_Version_From_Instance(access_token, instance_id, edition):
    '''
    Changes state of an instance to edition-confirmed so that it is assigned a version number
    Requires edition name & release date ("2021-07-08T00:00:00.000Z")
    Will currently just use current date as release date
    '''
    instance_url = 'https://publishing.ons.gov.uk/dataset/instances/' + instance_id
    headers = {'X-Florence-Token':access_token}
    
    current_date = datetime.datetime.now()
    release_date = datetime.datetime.strftime(current_date, '%Y-%m-%dT00:00:00.000Z')
    
    r = requests.put(instance_url, headers=headers, json={'edition':edition, 
                                                          'state':'edition-confirmed', 
                                                          'release_date': release_date})
    if r.status_code == 200:
        print('Instance state changed to edition-confirmed')
    else:
        raise Exception('Instance state not changed - returned a {} error'.format(r.status_code))
        

def Create_New_Dataset(access_token, dataset_id):
    '''
    Creates a new dataset in /dataset/datasets
    Used when adding a new dataset
    '''
    dataset_url = 'https://publishing.ons.gov.uk/dataset/datasets/' + dataset_id
    headers = {'X-Florence-Token':access_token}
    
    # Quick check to make sure it doesn't already exist
    r = requests.get(dataset_url, headers=headers)
    
    if r.status_code == 200: # expecting 404
        raise Exception('Dataset "{}" already exists'.format(dataset_id))
    
    r = requests.post(dataset_url, headers=headers, json={'id':dataset_id})
    if r.status_code == 201:
        print('Dataset - "{}" successfully created in dataset api'.format(dataset_id))
    else:
        print('Dataset - "{}" not created, returned a {} error'.format(dataset_id, r.status_code))


def Add_Data_To_Collection(credentials, dataset_id, instance_id, edition, collection_name):
    '''
    Creates a new collection within florence called collection_name
    Adds dataset to that new collection ready for metadata to be updated
    '''
    # Get access token
    access_token = Get_Access_Token(credentials)
    
    # Create new collection
    Create_Collection(access_token, collection_name)
    
    # Quick check to make sure collection was created
    Check_Collection_Exists(access_token, collection_name)
    
    # Return collection_id
    collection_id = Get_Collection_Id(access_token, collection_name)
    
    # Assigning instance a version number
    Create_New_Version_From_Instance(access_token, instance_id, edition)
    
    # Get new version number
    version_number = Get_Version_number(access_token, dataset_id, instance_id)
    
    # Add landing page to collection
    Add_Dataset_To_Collection(access_token, collection_id, dataset_id)
    
    # Add new version to collection
    Add_Dataset_Version_To_Collection(access_token, collection_id, dataset_id, edition, version_number)

    
def Upload_To_Cmd(credentials, dataset_id, edition, v4, metadata_file, collection_name):
    '''
    Full upload process - including metadata and adding to collection
    '''
    
    ### Upload data into cmd ###
    # get access_token
    access_token = Get_Access_Token(credentials)
    
    #quick check to make sure recipe exists in API
    Check_Recipe_Exists(access_token, dataset_id)
    
    # upload v4 into s3 bucket
    s3_url = Post_V4_To_S3(access_token, v4)
    
    # create new job
    job_id, instance_id = Post_New_Job(access_token, dataset_id, s3_url)
    
    # update state of job
    Update_State_Of_Job(access_token, job_id)
    
    ### Monitioring state of upload ###
    state_of_upload = '' # updated in while loop
    
    # start while loop
    while state_of_upload != 'completed':
        time.sleep(30) # checks every 30 seconds
        state_of_upload = Get_State_Of_Instance(access_token, instance_id)
    # Upload now complete
    
    ### Create and check collection ###
    # Create new collection
    Create_Collection(access_token, collection_name)
    
    # Quick check to make sure collection was created
    Check_Collection_Exists(access_token, collection_name)
    
    # Return collection_id
    collection_id = Get_Collection_Id(access_token, collection_name)
    
    ### Updating metadata main page ###
    # Reading in csv-w and formatting for the CMD API functions
    metadata_dict = Read_CSVW(metadata_file)
    
    # Updating general metadata
    Update_Metadata(access_token, dataset_id, metadata_dict)
    
    ### Attaching the instance to the newly created collection
    # Assigning instance a version number
    Create_New_Version_From_Instance(access_token, instance_id, edition)
    
    # Get new version number
    version_number = Get_Version_number(access_token, dataset_id, instance_id)
    
    # Add landing page to collection
    Add_Dataset_To_Collection(access_token, collection_id, dataset_id)
    
    # Add new version to collection
    Add_Dataset_Version_To_Collection(access_token, collection_id, dataset_id, edition, version_number)
    
    ### Updating final parts of metadata ###
    # Updating dimension metadata
    Update_Dimensions(access_token, dataset_id, instance_id, metadata_dict)
    
    # Update_Usage_Notes
    Update_Usage_Notes(access_token, dataset_id, version_number, metadata_dict, edition)
    

 
def Check_Upload_Dict(upload_dict):
    '''
    Checks upload_dict is in the correct format
    '''
    assert type(upload_dict) == dict, 'upload_dict must be a dict'
    
    for dataset in upload_dict.keys():
        assert type(upload_dict[dataset]) == dict, 'upload_dict[{}] must be a dict'.format(dataset)
        for key in ('v4', 'edition', 'collection_name', 'metadata_file'):
            assert key in upload_dict[dataset].keys(), 'upload_dict[{}] must have key - "{}"'.format(dataset, key)


def Multi_Upload_To_Cmd(credentials, upload_dict):
    '''
    Full upload process 
    Works for single or multiple uploads
    upload_dict is a dict of dicts with format:
    {
    dataset_id:
        {v4:'', 
        edition:'', 
        collection_name:'', 
        metadata_file:''
        }, 
    etc}
    '''
    
    # Quick check on upload_dict format
    Check_Upload_Dict(upload_dict)
    
    # get access_token
    access_token = Get_Access_Token(credentials)
    
    # Upload v4's all together
    for dataset_id in upload_dict.keys():
        
        # setting out variables
        v4 = upload_dict[dataset_id]['v4']
        
        # quick check to make sure recipe exists in API
        Check_Recipe_Exists(access_token, dataset_id)
        
        # upload v4 into s3 bucket
        s3_url = Post_V4_To_S3(access_token, v4)
        
        # create new job
        job_id, instance_id = Post_New_Job(access_token, dataset_id, s3_url)
        
        # update state of job
        Update_State_Of_Job(access_token, job_id)
        
        # updating some variables
        upload_dict[dataset_id]['s3_url'] = s3_url
        upload_dict[dataset_id]['job_id'] = job_id
        upload_dict[dataset_id]['instance_id'] = instance_id
        
        # small wait between uploads
        time.sleep(2)
        
        
    # Monitoring upload, adding metadata, adding data to collection
    for dataset_id in upload_dict.keys():
        
        # setting out variables
        v4 = upload_dict[dataset_id]['v4']
        instance_id = upload_dict[dataset_id]['instance_id']
        collection_name = upload_dict[dataset_id]['collection_name']
        metadata_file = upload_dict[dataset_id]['metadata_file']
        edition = upload_dict[dataset_id]['edition']
        
        # Monitioring state of upload #
        state_of_upload = '' # updated in while loop
        
        # start while loop
        while state_of_upload != 'completed':
            time.sleep(30) # checks every 30 seconds
            state_of_upload = Get_State_Of_Instance(access_token, instance_id)
        # Upload now complete
        
        # Create new collection
        Create_Collection(access_token, collection_name)
        
        # Quick check to make sure collection was created
        Check_Collection_Exists(access_token, collection_name)
        
        # Return collection_id
        collection_id = Get_Collection_Id(access_token, collection_name)
        
        # Reading in csv-w and formatting for the CMD API functions
        metadata_dict = Read_CSVW(metadata_file)
        
        # Updating general metadata
        Update_Metadata(access_token, dataset_id, metadata_dict)
        
        # Assigning instance a version number
        Create_New_Version_From_Instance(access_token, instance_id, edition)
        
        # Get new version number
        version_number = Get_Version_number(access_token, dataset_id, instance_id)
        
        # Add landing page to collection
        Add_Dataset_To_Collection(access_token, collection_id, dataset_id)
        
        # Add new version to collection
        Add_Dataset_Version_To_Collection(access_token, collection_id, dataset_id, edition, version_number)
        
        # Updating dimension metadata
        Update_Dimensions(access_token, dataset_id, instance_id, metadata_dict)
        
        # Update_Usage_Notes
        Update_Usage_Notes(access_token, dataset_id, version_number, metadata_dict, edition)
        
        # updating some variables
        upload_dict[dataset_id]['state_of_upload'] = state_of_upload
        upload_dict[dataset_id]['collection_id'] = collection_id 
        upload_dict[dataset_id]['version_number'] = version_number 
        
        
# TODO - full upload process for new dataset        


