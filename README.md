## About

This widget will display the count of your private messages on Yammer in the qtile status bar. Authentication credentials can be stored in a keyring or on disk depending on the setting of the 'keyring' parameter (default is to store in the keyring).

## How to use

Also, note that the first time you run the widget, you will need to authenticate. The widget will automatically pop an authentication  web page. Add your yammer login/password and authorize the widget to access your yammer data and you are good to go. Depending on the lifetime of the refresh_token, you may be required tore-authenticate periodically. After you are authenticated, the yammer data will be refreshed every 'update_interval' seconds.
