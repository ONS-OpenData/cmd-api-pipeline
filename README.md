# cmd-api-pipeline

Used to upload a v4 file(s) into CMD.

Florence access is required. Update the florence-info.json file with your login details.

Use either the functions Upload_To_Cmd or Multi_Upload_To_Cmd - Multi_Upload_To_Cmd can also upload a single dataset and is the preferred function.

#### How to use
- Updated florence-details.json with florence username and password
- Create a dict with relevant info for the upload - https://github.com/ONS-OpenData/cmd-api-pipeline/blob/master/cmd_api_pipeline.py#L1176-L1183
- Pass the path to florence-details.json and the dict to Multi_Upload_To_Cmd() - https://github.com/ONS-OpenData/cmd-api-pipeline/blob/master/cmd_api_pipeline.py#L1171

#### TODO
- There is some redundant functions that will be removed
- Some of the functions are used to do other 'stuff' that isn't uploading data into CMD, these will be separated in the future
- The functions will be turned into a python class
- Will be updated to use a service token instead of user credentials
- More robust checks will be added in
- Currently takes the metadata file in the format that is outputted from CMD, this is likely to change

