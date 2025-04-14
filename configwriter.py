from configparser import ConfigParser


def create_config():
    config = ConfigParser()
    config['database'] = {
        "database": "sites",
        "user": "myusername",
        "host": "127.0.0.1",
        "password": "mypassword!",
        "auth_plugin": 'mysql_native_password'
    }

    with open('config.yml', 'w') as configfile:
        config.write(configfile)


if __name__ == "__main__":
    create_config()
