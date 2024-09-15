# tranXformation

tranXformation allows you to define a simple playbook of transformations on a CSV or Excel document. Often, repetitive and tedious tasks need to be performed, which, although Excel can handle, may not always be practical. tranXformation was primarily developed to split cells into multiple rows, for example, when a cell contains several comma-separated values, and to move information between columns based on various parameters.

<p align="center">
  <img src="images/tranXformation-logo.jpeg" alt="tranXformation" width="300"/>
</p>

## TranXformation Operations

### Explode 

##### Operator: "explode_into_rows"

The `explode_into_rows` operator is used to transform each element of a list-like column into a separate row, replicating the rest of the columns as needed. This is especially useful when you have a column where each row contains multiple values (e.g., a list or a set), and you want to "unpack" those values into individual rows.

### Split

##### Operator: "split_into_columns"

The `split_into_columns` operator is ofen used to split a string from a column into multiple columns based on a delimiter. This is particularly useful when dealing with data where a single column contains concatenated values that need to be separated into distinct columns.

### Rename

##### Operator: "rename_column"

The `rename_column` operator allows you to change the names of one or more columns in a DataFrame. This is particularly useful when you need to standardize column names, correct typos, or make column names more descriptive.

### Create

##### Operator: "create_column"

The `create_column` operator is used to create a new column with this operator.

### Conditional Tagging

##### Operator: "conditional_tagging"

`conditional_tagging` is an operator used to create new columns or update column values where values are assigned based on conditions related to other columns. This is useful when you want to classify or "tag" rows in your dataset depending on the values in one or more columns.

## TranXformation Summaries

The primary goal of **tranXformation** is not to create visualizations; however, it is offered as an option to automatically generate certain groupings and assist in verifying the generated data. There are different options available for creating charts, with a limitation of up to two levels of grouping.

Available options:

#### Filter

The filter is used to incorporate customization into the grouping.


## Usage Instructions

The usage instructions are available in the help section. To access them, run the following command:

```bash
python tranXformation.py --help
```

<pre>
Usage: tranXformation.py [options] input_file_excel_or_csv

Options:
  -h, --help            show this help message and exit
  -f FORMAT, --format=FORMAT
                        Set the input and output format. Valid values: 'excel'
                        and 'csv' (defaul: 'excel').
  -o FILE, --output=FILE
                        Specify the output filename (default:
                        20240915_000102). '.xlsx' or '.csv will be added based
                        on selected format.
  -l LEVEL, --loglevel=LEVEL
                        Set the logging level (DEBUG, INFO, WARNING, ERROR,
                        CRITICAL)
  -c FILE, --config=FILE
                        Path to the configuration file
</pre>


## Configuration File

> **Note:** Copy the cofiguration template and remove the ".template" suffix. Manage multiple configuration files and specify what to use in command parameter (-c).

Example of configuration file:

```
# Transformation occurs in order

tranformatations:

  - column: Name
    operation: explode_into_rows
    separator: ','

  - column: Full_Name
    operator: split_into_columns
    separator: '/'
    destination_columns:
      - Subsidiary
      - Country

  - column: Name
      operation: rename_column
      renamed_column_name: 'First Name'

  - column: new_data
    operation: create_column
    generate_random: True

  - column: Boy_or_Girl
    operation: conditional_tagging
    destination_column: Genre
    conditions:
      - if_value: 'Boy'
        set: Male
      - if_value: 'Girl'
        set: Female
      - else: 'Not Classified'

summaries:

  - title: Genre Distribution
    groupby:
      - Genre

  - title: Genre and First Name Distribution
    groupby:
      - Genre
      - First Name

  - title: Genre Distribution but no First Name Jhon
    filter: 
      column: 'First Name'
      operator: '!='
      value: 'Jhon'
    groupby:
      - Genre

```

## Windows Users (no developers)

Bundled binary version of the application for Windows is provided to prevent script users from needing to install Python and its libraries.

### User Instruction

#### 1. Copy executable

Copy the executable `tranXforamtion.exe` located in the `dist` folder to a folder of your choice. For example, create a folder named **tranXformation** on your desktop and copy the .exe file there.

#### 2. Add Configuration File

You can place the configuration file `config.yml` in the same directory, and it will be used by default. Alternatively, you can use other configuration files and specify them with the -c option.

#### 3. Terminal Usage (CMD)

Open a terminal or command prompt (`CMD`). Navigate to the directory and run the executable.

### Developer Instructions

The bundle version is located in the `dist` directory and was created using the following command on a Windows system:

#### 1. Install PyInstaller

```bash
pip install pyinstaller
```

#### 2. Create the Executable

```bash
pyinstaller --onefile --icon=images\tranXformation-logo.ico tranXformation.py
```

## Setup Instructions

#### 1. Create and Activate a Virtual Environment

It is recommended to use a virtual environment to keep the dependencies isolated.

- **On Windows**:

  Open a terminal or command prompt and run the following commands:

  ```bash
  python -m venv venv
  .\venv\Scripts\activate
  ```

- **On macOS/Linux**:

    Open a terminal and run the following commands:

    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

#### 2. Install Dependencies

Once the virtual environment is activated, install the required dependencies listed in the requirements.txt file:

```bash
pip install -r requirements.txt
```

This will install all the necessary libraries to run tranXformation.

#### 3. Deactivate the Virtual Environment

When you're done working, you can deactivate the virtual environment by simply running:

```bash
deactivate
```
