# pls

> An automation tool for organizing directories

## Installation

```
git clone https://github.com/masef3/pls.git
cd pls
pip install -r requirements.txt
```

## Features

- Group files into subfolders based on their extensions.
- Clean up empty directories automatically.
- Watch directory changes in real-time.

## Usage
` pls [Command] [Flags] `

## Commands
* **`pls show`**  
  Prints the active working directory.

* **`pls change [path]`**  
  Updates the target folder permanently. If no path is provided, resets to `~`.

* **`pls clean`**  
  Scans the directory and moves files into extension-based subdirectories.

* **`pls cleanbg`**  
  Starts background execution to sort files automatically.

* **`pls watch`**  
  Monitors folder changes in real-time and prints activity to stdout.

* **`pls recycle`**  
  Finds and removes any empty subdirectories in the target path.
