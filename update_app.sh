#!/bin/bash
# # set some environmental variables # NOT WORKING
# cat set_env.sh | /bin/bash;

# activate the virtual environment
source env/bin/activate;

# install dependencies
pip install -r requirements.txt;

# migrate the database
python manage.py migrate;

# collect static files
python manage.py collectstatic --clear --noinput;

# import dynamicmodels_data
python manage.py import_dynamicmodels_data

# import menu data
python manage.py Import_Menu_Data;



### To use this run 
### /bin/bash update_app.sh  
### restart services, Ex:
### sudo systemctl restart smartship-development.socket smartship-development.service nginx.service;
### sudo systemctl restart smartship-testing.socket smartship-testing.service nginx.service;
### sudo systemctl restart smartship-staging.socket smartship-staging.service nginx.service;
