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
    
    r = requests.get(recipe_api_url + '?limit=1000', headers=headers, verify=False)
    
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
    
    r = requests.get(single_recipe_url, headers=headers, verify=False)
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
    
    r = requests.put(single_recipe_url, headers=headers, json=updated_recipe_dict, verify=False)
    
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
    
    r = requests.put(single_recipe_url, headers=headers, json=new_editions_dict, verify=False)
    
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
    
    r = requests.put(single_recipe_url, headers=headers, json=codelist_changes_dict, verify=False)
    
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
    
    r = requests.post(recipe_api_url, headers=headers, json=recipe_dict, verify=False)
    
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
            loop_dict['is_hierarchy'] = 'true'
        
        recipe_codelists.append(loop_dict)
    recipe_dict['output_instances'][0]['code_lists'] = recipe_codelists
    
    return recipe_dict


def Get_Dataset_Instances_Api(access_token):
    ''' 
    Returns /dataset/instances API 
    '''
    dataset_instances_api_url = 'https://publishing.ons.gov.uk/dataset/instances'
    headers = {'X-Florence-Token':access_token}
    
    r = requests.get(dataset_instances_api_url + '?limit=1000', headers=headers, verify=False)
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
                new_dict = requests.get(new_url, headers=headers, verify=False).json()
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
    
    r = requests.get(dataset_instances_url, headers=headers, verify=False)
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
    
    r = requests.get(dataset_jobs_api_url + '?limit=1000', headers=headers, verify=False)
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
                new_dict = requests.get(new_url, headers=headers, verify=False).json()
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
        
    r = requests.post(dataset_jobs_api_url, headers=headers, json=new_job_json, verify=False)
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
        return job_id


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

    r = requests.put(attaching_file_to_job_url, headers=headers, json=added_file_json, verify=False)
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
        r = requests.put(updating_state_of_job_url, headers=headers, json=updating_state_of_job_json, verify=False)
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
    
    r = requests.get(dataset_jobs_id_url, headers=headers, verify=False)
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
    job_id = Post_New_Job(access_token, dataset_id, s3_url)
    
    # update state of job
    Update_State_Of_Job(access_token, job_id)


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
            r = requests.post(upload_url, headers=headers, params=params, files=files, verify=False)
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
    



