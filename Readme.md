For reading the CSV from Cloud object storage.

## Set the right project
ibmcloud ce project select -n HSE_Learning_Project

## Deploying the function
ibmcloud ce fn create -n cloud-object-reader-watsonx -runtime python-3.11 --build-source https://github.com/RahulGanguli24/WatsonX-Cognos-Export-Reader.git --build-context-dir /
