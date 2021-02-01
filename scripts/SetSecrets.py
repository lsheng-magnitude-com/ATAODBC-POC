import os
import Remove
import re
import sys
import fileinput


def read_env_variable(var):
    if os.environ.get(var, 'undef') != 'undef':
        print (var + ' is set')
    else:
        print (var + ' not set')


def main():
    SNOWFLAKE_TEST_USER
    SNOWFLAKE_TEST_PASSWORD
    SNOWFLAKE_TEST_ACCOUNT
    SNOWFLAKE_TEST_WAREHOUSE
    SNOWFLAKE_TEST_DATABASE
    SNOWFLAKE_TEST_SCHEMA
    SNOWFLAKE_TEST_ROLE


if __name__ == "__main__":
    main()
