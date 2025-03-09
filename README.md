Screenshot and send picture to AI.

This app was tested on Windows. It may, in theory, also work on MacOS and Linux X11 but that has not been verified.

## Demo

https://github.com/user-attachments/assets/0ef76b38-4e4c-4168-b222-d1f37dfcd3a3

## Installation

### Python

```bash
pip install git+https://github.com/ndtoan96/smartcap-py.git
```

### Prebuilt binary

You can download prebuilt binary from the
[release](https://github.com/ndtoan96/smartcap-py/releases) page.

## Setup

Go to [Google AI studio](https://aistudio.google.com/app/apikey) to get an API
key. It's free. Then run the app for the first time, screenshot any image. Then
after the prompt window opens, navigate to the **config** tab and enter the API
key.

![image](https://github.com/user-attachments/assets/68b5eb7a-7e44-46c6-84ee-e2a8722dbca2)

## Usage

Run the executable directly. Or if you install from pip, run
`python -m smartcap`.

## Tips

- You can create a global shortcut for this app on Windows by creating a
  shortcut file, place it on Desktop, then right click > properties > Shortcut
  key and enter you shortcut key. Log out and log in again for the setting to
  take effect.
- You can press Ctrl-Enter to quickly send the prompt instead of clicking the
  send button.
