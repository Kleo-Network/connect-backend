# how to start server

```
pipenv shell
python3 run.py
```

[![The MIT License](https://img.shields.io/badge/license-MIT-orange.svg?style=flat-square)](LICENSE)

  Flask Boilerplate to quickly get started with production grade flask application with some additional packages and configuration prebuilt.

  You can find an in-depth article on this implementation [here](https://dev.to/idrisrampurawala/flask-boilerplate-structuring-flask-app-3kcd).

# Contributing
  We encourage you to contribute to Flask Boilerplate! Please check out the [Contributing](CONTRIBUTING.md) guidelines about how to proceed.

# Getting Started

### Prerequisites

- Python 3.11.3 or higher
- Up and running Redis client

### Project setup
```sh
# clone the repo
$ git clone https://github.com/idris-rampurawala/flask-boilerplate.git
# move to the project folder
$ cd flask-boilerplate
```
If you want to install redis via docker
```sh
$ docker run -d --name="flask-boilerplate-redis" -p 6379:6379 redis
```

### Creating virtual environment

- Install `pipenv` a global python project `pip install pipenv`
- Create a `virtual environment` for this project
```shell
# creating pipenv environment for python 3
$ pipenv --three
# activating the pipenv environment
$ pipenv shell
# install all dependencies (include -d for installing dev dependencies)
$ pipenv install -d

# if you have multiple python 3 versions installed then
$ pipenv install -d --python 3.11
```
### Configuration

- There are 3 configurations `development`, `staging` and `production` in `config.py`. Default is `development`
- Create a `.env` file from `.env.example` and set appropriate environment variables before running the project

### Running app

- Run flask app `python run.py`
- Logs would be generated under `log` folder

### Running celery workers

- Run redis locally before running celery worker
- Celery worker can be started with following command
```sh
# run following command in a separate terminal
$ celery -A celery_worker.celery worker --loglevel='INFO'  
# (append `--pool=solo` for windows)
```


# Preconfigured Packages
Includes preconfigured packages to kick start flask app by just setting appropriate configuration.

| Package 	| Usage 	|
|-----	|-----	|
| [celery](https://docs.celeryproject.org/en/stable/getting-started/introduction.html) 	| Running background tasks 	|
| [redis](https://redislabs.com/lp/python-redis/) 	| A Python Redis client for caching 	|
| [flask-cors](https://flask-cors.readthedocs.io/) 	| Configuring CORS 	|
| [python-dotenv](https://pypi.org/project/python-dotenv/) 	| Reads the key-value pair from .env file and adds them to environment variable. 	|
| [marshmallow](https://marshmallow.readthedocs.io/en/stable/) 	| A package for creating Schema, serialization, deserialization 	|
| [webargs](https://webargs.readthedocs.io/) 	| A Python library for parsing and validating HTTP request objects 	|

`autopep8` & `flake8` as `dev` packages for `linting and formatting`

# Test
  Test if this app has been installed correctly and it is working via following curl commands (or use in Postman)
- Check if the app is running via `status` API
```shell
$ curl --location --request GET 'http://localhost:5000/status'
```
- Check if core app API and celery task is working via
```shell
$ curl --location --request GET 'http://localhost:5000/api/v1/core/test'
```
- Check if authorization is working via (change `API Key` as per you `.env`)
```shell
$ curl --location --request GET 'http://localhost:5000/api/v1/core/restricted' --header 'x-api-key: 436236939443955C11494D448451F'
```

# Contract Document
Base path for all APIs: **[https://api.kleo.network/](https://api.kleo.network/)**


## User APIs
1. Get user details from solana address[signup/login]


#### **Description:**


<table>
  <tr>
   <td><strong>path</strong>
   </td>
   <td><strong>api/v1/core/user/create-user</strong>
   </td>
  </tr>
  <tr>
   <td><strong>Type</strong>
   </td>
   <td>POST
   </td>
  </tr>
  <tr>
   <td><strong>Description</strong>
   </td>
   <td>To fetch user details from the DB
   </td>
  </tr>
  <tr>
   <td><strong>Header</strong>
   </td>
   <td>No header
   </td>
  </tr>
  <tr>
   <td><strong>Path Variable</strong>
   </td>
   <td>No
   </td>
  </tr>
</table>



#### **Body Param:**


<table>
  <tr>
   <td><strong>No</strong>
   </td>
   <td><strong>Param name</strong>
   </td>
   <td><strong>type</strong>
   </td>
   <td><strong>Description</strong>
   </td>
   <td><strong>Required</strong>
   </td>
  </tr>
  <tr>
   <td>1
   </td>
   <td>Address
   </td>
   <td>String
   </td>
   <td>Solana address of the user
   </td>
   <td>True
   </td>
  </tr>
  <tr>
   <td>2
   </td>
   <td>signup
   </td>
   <td>Boolean
   </td>
   <td>Flag for the user creation for signup
   </td>
   <td>False
   </td>
  </tr>
</table>


#### **Example:**


<table>
  <tr>
   <td>1.
   </td>
   <td>Sign up
   </td>
   <td>{
<p>
    “address”:  “2aNXZ2gicvGkF7CyzBK8qguA6ycoXMcgw7usvLBRZiFK”
<p>
    “signup”: true
<p>
}
   </td>
  </tr>
  <tr>
   <td>2.
   </td>
   <td>Login
   </td>
   <td>{
<p>
   “address”: “DRerVGgicvGkF7BRfyK8qguA6ycoXMcgw7usvLBhdEDC”
<p>
}
   </td>
  </tr>
</table>



#### **Response**:


<table>
  <tr>
   <td>No
   </td>
   <td>Status Code
   </td>
   <td>Response
   </td>
  </tr>
  <tr>
   <td>1.
   </td>
   <td>200
   </td>
   <td>{
<p>
   address:  “2aNXZ2gicvGkF7CyzBK8qguA6ycoXMcgw7usvLBRZiFK”,
<p>
   name: “”
<p>
   verified: false
<p>
   last_cards_marked: 0
<p>
   about: “”
<p>
   pfp: “”
<p>
   content_tags: []
<p>
   last_attested: 0
<p>
   identity_tags: []
<p>
   badges: []
<p>
   Profile_metadata: {}
<p>
},
<p>
{
<p>
   address:  “2aNXZ2gicvGkF7CyzBK8qguA6ycoXMcgw7usvLBRZiFK”,
<p>
   name: “Mark Status”,
<p>
   verified: false
<p>
   last_cards_marked: 1703721486
<p>
   about: “Exploring the world of Solana and building cool projects”
<p>
   pfp: “https://pbs.twimg.com/profile\_images/1590877918015926272/Xl2Bd-X2\_400x400.jpg”
<p>
   content_tags: [ “solana”, “nft” ]
<p>
   last_attested: 1703721486
<p>
   identity_tags: [“developer”, “SDE”]
<p>
   Badges: [“bonk]
<p>
   Profile_metadata: {}
<p>
}
   </td>
  </tr>
  <tr>
   <td>2.
   </td>
   <td>400
   </td>
   <td>{"error": "Missing required parameters"}
   </td>
  </tr>
</table>




2. Update user details at signup phase 2


#### **Description:**


<table>
  <tr>
   <td><strong>path</strong>
   </td>
   <td><strong>api/v1/core/update-user/&lt;address></strong>
   </td>
  </tr>
  <tr>
   <td><strong>Type</strong>
   </td>
   <td>PUT
   </td>
  </tr>
  <tr>
   <td><strong>Description</strong>
   </td>
   <td>To update user details from the DB
   </td>
  </tr>
  <tr>
   <td><strong>Header</strong>
   </td>
   <td>Jwt token
   </td>
  </tr>
</table>



#### **Path Param:**


<table>
  <tr>
   <td><strong>No</strong>
   </td>
   <td><strong>Param name</strong>
   </td>
   <td><strong>type</strong>
   </td>
   <td><strong>Description</strong>
   </td>
   <td><strong>Required</strong>
   </td>
  </tr>
  <tr>
   <td>1`
   </td>
   <td>address
   </td>
   <td>String
   </td>
   <td>Solana address of the user
   </td>
   <td>True
   </td>
  </tr>
</table>



#### **Body Param:**


<table>
  <tr>
   <td><strong>No</strong>
   </td>
   <td><strong>Param name</strong>
   </td>
   <td><strong>type</strong>
   </td>
   <td><strong>Description</strong>
   </td>
   <td><strong>Required</strong>
   </td>
  </tr>
  <tr>
   <td>1
   </td>
   <td>about
   </td>
   <td>String
   </td>
   <td>Bio for user
   </td>
   <td>True
   </td>
  </tr>
  <tr>
   <td>2
   </td>
   <td>name
   </td>
   <td>String
   </td>
   <td>Name of user
   </td>
   <td>True
   </td>
  </tr>
  <tr>
   <td>3
   </td>
   <td>pfp
   </td>
   <td>String
   </td>
   <td>Url for user image
   </td>
   <td>True
   </td>
  </tr>
  <tr>
   <td>4
   </td>
   <td>content_tags
   </td>
   <td>List of strings
   </td>
   <td>Tags which represents the content
   </td>
   <td>False
   </td>
  </tr>
  <tr>
   <td>5
   </td>
   <td>identity_tags
   </td>
   <td>List of strings
   </td>
   <td>Tags which represents the user
   </td>
   <td>False
   </td>
  </tr>
  <tr>
   <td>6
   </td>
   <td>Profile_metadata
   </td>
   <td>Json
   </td>
   <td>Metadata of user
   </td>
   <td>False
   </td>
  </tr>
</table>


#### **Example:**


<table>
  <tr>
   <td>1.
   </td>
   <td>Update user details
   </td>
   <td>{
<p>
   about: “Exploring the world of Solana and building cool projects”
<p>
   pfp: “https://pbs.twimg.com/profile\_images/1590877918015926272/Xl2Bd-X2\_400x400.jpg”
<p>
   content_tags: [ “solana”, “nft” ]
<p>
   identity_tags: [“developer”, “SDE”]
<p>
   Profile_metadata: {}
<p>
}
   </td>
  </tr>
</table>



#### **Response:**


<table>
  <tr>
   <td><strong>No</strong>
   </td>
   <td><strong>Status Code</strong>
   </td>
   <td><strong>Response</strong>
   </td>
  </tr>
  <tr>
   <td>1.
   </td>
   <td>200
   </td>
   <td>{
<p>
   address:  “2aNXZ2gicvGkF7CyzBK8qguA6ycoXMcgw7usvLBRZiFK”,
<p>
   name: “Mark Status”,
<p>
   verified: false
<p>
   last_cards_marked: 1703721486
<p>
   about: “Exploring the world of Solana and building cool projects”
<p>
   pfp: “https://pbs.twimg.com/profile\_images/1590877918015926272/Xl2Bd-X2\_400x400.jpg”
<p>
   content_tags: [ “solana”, “nft” ]
<p>
   last_attested: 1703721486
<p>
   identity_tags: [“developer”, “SDE”]
<p>
   Badges: [“bonk]
<p>
   Profile_metadata: {}
<p>
}
   </td>
  </tr>
  <tr>
   <td>2.
   </td>
   <td>400
   </td>
   <td>{"error": "Missing required parameters"}
   </td>
  </tr>
</table>



## Card APIs



3. Get user published card details


#### **Description**


<table>
  <tr>
   <td><strong>path</strong>
   </td>
   <td><strong>api/v1/core/cards/published/&lt;address></strong>
   </td>
  </tr>
  <tr>
   <td><strong>Type</strong>
   </td>
   <td>GET
   </td>
  </tr>
  <tr>
   <td><strong>Description</strong>
   </td>
   <td>To fetch published card from the DB
   </td>
  </tr>
  <tr>
   <td><strong>Header</strong>
   </td>
   <td>Jwt token
   </td>
  </tr>
</table>



#### **Path Param**


<table>
  <tr>
   <td><strong>No</strong>
   </td>
   <td><strong>Param name</strong>
   </td>
   <td><strong>type</strong>
   </td>
   <td><strong>Description</strong>
   </td>
   <td><strong>Required</strong>
   </td>
  </tr>
  <tr>
   <td>1`
   </td>
   <td>address
   </td>
   <td>String
   </td>
   <td>Solana address of the user
   </td>
   <td>True
   </td>
  </tr>
</table>



#### **Response:**


<table>
  <tr>
   <td><strong>No</strong>
   </td>
   <td><strong>Status Code</strong>
   </td>
   <td><strong>Response</strong>
   </td>
  </tr>
  <tr>
   <td>1.
   </td>
   <td>200 [List of json cards]
   </td>
   <td>[{
<p>
   date: “11 Feb 2024”,
<p>
   cardType: “DataCard”,
<p>
   category: “Information Technology”,
<p>
   content: “Visits to huggingface.co increased by”
<p>
   metadata: {
<p>
       contentImageUrl: “”,
<p>
       contentData: “30%”
<p>
       likeCount: 15,
<p>
       shareCount: 20,
<p>
       digCount: 15
<p>
   }
<p>
}]
   </td>
  </tr>
  <tr>
   <td>2.
   </td>
   <td>400
   </td>
   <td>{"error": "Missing required parameters"}
   </td>
  </tr>
</table>




4. Delete published card details for any user


#### **Description**


<table>
  <tr>
   <td><strong>path</strong>
   </td>
   <td><strong>api/v1/core/cards/published/&lt;address></strong>
   </td>
  </tr>
  <tr>
   <td><strong>Type</strong>
   </td>
   <td>DELETE
   </td>
  </tr>
  <tr>
   <td><strong>Description</strong>
   </td>
   <td>To delete published card from the DB for any user before card is not attested
   </td>
  </tr>
  <tr>
   <td><strong>Header</strong>
   </td>
   <td>Jwt token
   </td>
  </tr>
</table>



#### **Path Param**


<table>
  <tr>
   <td><strong>No</strong>
   </td>
   <td><strong>Param name</strong>
   </td>
   <td><strong>type</strong>
   </td>
   <td><strong>Description</strong>
   </td>
   <td><strong>Required</strong>
   </td>
  </tr>
  <tr>
   <td>1`
   </td>
   <td>address
   </td>
   <td>String
   </td>
   <td>Solana address of the user
   </td>
   <td>True
   </td>
  </tr>
</table>



#### **Body Param**


<table>
  <tr>
   <td><strong>No</strong>
   </td>
   <td><strong>Param name</strong>
   </td>
   <td><strong>type</strong>
   </td>
   <td><strong>Description</strong>
   </td>
   <td><strong>Required</strong>
   </td>
  </tr>
  <tr>
   <td>1`
   </td>
   <td>ids
   </td>
   <td>List of strings
   </td>
   <td>List of ids for published cards
   </td>
   <td>True
   </td>
  </tr>
</table>



#### **Response:**


<table>
  <tr>
   <td><strong>No</strong>
   </td>
   <td><strong>Status Code</strong>
   </td>
   <td><strong>Response</strong>
   </td>
  </tr>
  <tr>
   <td>1.
   </td>
   <td>200 
   </td>
   <td>{"message": "&lt;count of deleted cards> published cards deleted from db for &lt;user_address>"}
   </td>
  </tr>
  <tr>
   <td>2.
   </td>
   <td>400
   </td>
   <td>{"error": "Missing required parameters"}
   </td>
  </tr>
</table>




5. Get user pending card details


#### **Description**


<table>
  <tr>
   <td><strong>path</strong>
   </td>
   <td><strong>api/v1/core/cards/pending/&lt;address></strong>
   </td>
  </tr>
  <tr>
   <td><strong>Type</strong>
   </td>
   <td>GET
   </td>
  </tr>
  <tr>
   <td><strong>Description</strong>
   </td>
   <td>To fetch pending card from the DB
   </td>
  </tr>
  <tr>
   <td><strong>Header</strong>
   </td>
   <td>Jwt token
   </td>
  </tr>
</table>



#### **Path Param**


<table>
  <tr>
   <td><strong>No</strong>
   </td>
   <td><strong>Param name</strong>
   </td>
   <td><strong>type</strong>
   </td>
   <td><strong>Description</strong>
   </td>
   <td><strong>Required</strong>
   </td>
  </tr>
  <tr>
   <td>1`
   </td>
   <td>address
   </td>
   <td>String
   </td>
   <td>Solana address of the user
   </td>
   <td>True
   </td>
  </tr>
</table>



#### **Response:**


<table>
  <tr>
   <td><strong>No</strong>
   </td>
   <td><strong>Status Code</strong>
   </td>
   <td><strong>Response</strong>
   </td>
  </tr>
  <tr>
   <td>1.
   </td>
   <td>200 [List of json cards]
   </td>
   <td>[{
<p>
   date: “11 Feb 2024”,
<p>
   userName: “Den Brown”,
<p>
   userPfp: “https://pbs.twimg.com/profile\_images/1590877918015926272/Xl2Bd-X2\_400x400.jpg”
<p>
   content: “Visits to huggingface.co increased by”
<p>
   links: {
<p>
       domain: 'www.huggingface.co',
<p>
       title: 'Hugging Face – The AI community building the future.'
<p>
   }
<p>
}]
   </td>
  </tr>
  <tr>
   <td>2.
   </td>
   <td>400
   </td>
   <td>{"error": "Missing required parameters"}
   </td>
  </tr>
</table>




6. Delete pending card details for any user


#### **Description**


<table>
  <tr>
   <td><strong>path</strong>
   </td>
   <td><strong>api/v1/core/cards/pending/&lt;address></strong>
   </td>
  </tr>
  <tr>
   <td><strong>Type</strong>
   </td>
   <td>DELETE
   </td>
  </tr>
  <tr>
   <td><strong>Description</strong>
   </td>
   <td>To delete removed pending card from the DB for any user
   </td>
  </tr>
  <tr>
   <td><strong>Header</strong>
   </td>
   <td>Jwt token
   </td>
  </tr>
</table>



#### **Path Param**


<table>
  <tr>
   <td><strong>No</strong>
   </td>
   <td><strong>Param name</strong>
   </td>
   <td><strong>type</strong>
   </td>
   <td><strong>Description</strong>
   </td>
   <td><strong>Required</strong>
   </td>
  </tr>
  <tr>
   <td>1`
   </td>
   <td>address
   </td>
   <td>String
   </td>
   <td>Solana address of the user
   </td>
   <td>True
   </td>
  </tr>
</table>



#### **Body Param**


<table>
  <tr>
   <td><strong>No</strong>
   </td>
   <td><strong>Param name</strong>
   </td>
   <td><strong>type</strong>
   </td>
   <td><strong>Description</strong>
   </td>
   <td><strong>Required</strong>
   </td>
  </tr>
  <tr>
   <td>1`
   </td>
   <td>ids
   </td>
   <td>List of strings
   </td>
   <td>List of ids for pending cards
   </td>
   <td>True
   </td>
  </tr>
</table>



#### **Response:**


<table>
  <tr>
   <td><strong>No</strong>
   </td>
   <td><strong>Status Code</strong>
   </td>
   <td><strong>Response</strong>
   </td>
  </tr>
  <tr>
   <td>1.
   </td>
   <td>200 
   </td>
   <td>{"message": "&lt;count of deleted cards> pending cards deleted from db for &lt;user_address>"}
   </td>
  </tr>
  <tr>
   <td>2.
   </td>
   <td>400
   </td>
   <td>{"error": "Missing required parameters"}
   </td>
  </tr>
</table>




7. Get all cards and user details of any user


#### **Description**


<table>
  <tr>
   <td><strong>path</strong>
   </td>
   <td><strong>api/v1/core/user/&lt;address>/published-cards/info</strong>
   </td>
  </tr>
  <tr>
   <td><strong>Type</strong>
   </td>
   <td>GET
   </td>
  </tr>
  <tr>
   <td><strong>Description</strong>
   </td>
   <td>To all published card and user from the DB
   </td>
  </tr>
  <tr>
   <td><strong>Header</strong>
   </td>
   <td>Jwt token
   </td>
  </tr>
</table>



#### **Path Param**


<table>
  <tr>
   <td><strong>No</strong>
   </td>
   <td><strong>Param name</strong>
   </td>
   <td><strong>type</strong>
   </td>
   <td><strong>Description</strong>
   </td>
   <td><strong>Required</strong>
   </td>
  </tr>
  <tr>
   <td>1`
   </td>
   <td>address
   </td>
   <td>String
   </td>
   <td>Solana address of the user
   </td>
   <td>True
   </td>
  </tr>
</table>



#### **Response:**


<table>
  <tr>
   <td><strong>No</strong>
   </td>
   <td><strong>Status Code</strong>
   </td>
   <td><strong>Response</strong>
   </td>
  </tr>
  <tr>
   <td>1.
   </td>
   <td>200 
   </td>
   <td>{
<p>
    "published_cards": [
<p>
        {
<p>
            "cardType": "DataCard",
<p>
            "category": "",
<p>
            "content": "Visits to huggingface.co increased by",
<p>
            "date": "18 Mar 2024",
<p>
            "metadata": {
<p>
                "contentData": "30%",
<p>
                "contentImageUrl": "",
<p>
                "digCount": 15,
<p>
                "likeCount": 15,
<p>
                "shareCount": 20
<p>
            }
<p>
        },
<p>
        {
<p>
            "cardType": "ImageCard",
<p>
            "category": "",
<p>
            "content": "New ML model architecture released",
<p>
            "date": "19 Mar 2024",
<p>
            "metadata": {
<p>
                "contentData": "",
<p>
                "contentImageUrl": "https://example.com/image1.jpg",
<p>
                "digCount": 20,
<p>
                "likeCount": 25,
<p>
                "shareCount": 30
<p>
            }
<p>
        },
<p>
        {
<p>
            "cardType": "DomainVisitCard",
<p>
            "category": "",
<p>
            "content": "Visits to openai.com",
<p>
            "date": "20 Mar 2024",
<p>
            "metadata": {
<p>
                "contentData": "50,000 visits",
<p>
                "contentImageUrl": "",
<p>
                "digCount": 10,
<p>
                "likeCount": 10,
<p>
                "shareCount": 15
<p>
            }
<p>
        }
<p>
    ],
<p>
    "user": {
<p>
        "about": "developer with 1 YOE in java",
<p>
        "address": "7B3FeQJ2SZa4Tw9gJXu7zzdmivY9ot17uXSCko1zMefh",
<p>
        "badges": [
<p>
            "bonk",
<p>
            "bonk_v2"
<p>
        ],
<p>
        "content_tags": [
<p>
            "java",
<p>
            "springBoot"
<p>
        ],
<p>
        "identity_tags": [
<p>
            "developer",
<p>
            "backend"
<p>
        ],
<p>
        "last_attested": 1710738880,
<p>
        "last_cards_marked": 1710738880,
<p>
        "name": "den marchov",
<p>
        "pfp": "https://images.pexels.com/photos/7562313/pexels-photo-7562313.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=1",
<p>
        "profile_metadata": {
<p>
            "alt_image_tag": "7B3FeQJ2SZa4Tw9gJXu7zzdmivY9ot17uXSCko1zMefd"
<p>
        },
<p>
        "verified": false
<p>
    }
<p>
}
   </td>
  </tr>
  <tr>
   <td>2.
   </td>
   <td>400
   </td>
   <td>{"error": "Missing required parameters"}
   </td>
  </tr>
  <tr>
   <td>3
   </td>
   <td>404
   </td>
   <td>If we do not pass users in 
   </td>
  </tr>
</table>

# License
 This program is free software under MIT license. Please see the [LICENSE](LICENSE) file in our repository for the full text.
