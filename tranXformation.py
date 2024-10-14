#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import optparse
import logging
import yaml
import warnings
import string
import random
from datetime import datetime

import pandas as pd

import openpyxl
from openpyxl.chart import PieChart, Reference
from openpyxl.utils.dataframe import dataframe_to_rows

import operator

OPS = {
    '==': operator.eq,
    '!=': operator.ne,
    '>': operator.gt,
    '>=': operator.ge,
    '<': operator.lt,
    '<=': operator.le,
    '+': operator.add,
    '-': operator.sub,
    '*': operator.mul,
    '/': operator.truediv,
}


def parse_arguments(arguments):
    """
    Parse the arguments passed to the script.
    Returns the parsed options.
    """

    # Create an OptionParser object
    parser = optparse.OptionParser(
        usage="usage: %prog [options] input_file_excel_or_csv")

    parser.add_option(
        '-f', '--format',
        dest='format',
        default='excel',
        type="string",
        help="Set the input and output format. Valid values: 'excel' and 'csv' (defaul: 'excel')."
    )

    parser.add_option(
        "-o", "--output",
        dest="output_filename",
        default=datetime.now().strftime("%Y%m%d_%H%M%S"),  # Current timestamp
        help=f"Specify the output filename (default: current timestamp). '.xlsx' or '.csv will be added based on selected format.",
        metavar="FILE"
    )

    parser.add_option(
        "-l", "--loglevel",
        dest="log_level",
        default="INFO",
        help="Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
        metavar="LEVEL"
    )

    parser.add_option(
        "-c", "--config",
        dest="config_file",
        default="config.yml",
        help="Path to the configuration file",
        metavar="FILE"
    )

    (options, args) = parser.parse_args()

    # Check if at least one positional argument was passed
    if len(args) < 1:
        parser.error("At least one parameter is required")

    # Get the parameter (first positional argument)
    parameter = args[0]

    # Check if the provided mode is valid
    valid_formats = ['excel', 'csv']
    if options.format not in valid_formats:
        print(
            f"Error: Invalid format '{options.format}'. Valid modes are: {', '.join(valid_formats)}")
        sys.exit(1)

    return parameter, options


def load_excel_file(excel_file, sheet_name=None):

    # Suppress specific warning from openpyxl
    warnings.filterwarnings(
        "ignore", message="Workbook contains no default style, apply openpyxl's default")

    # Check if the file exists
    if not os.path.isfile(excel_file):
        logging.error(f"Error: The file '{excel_file}' does not exist.")
        return None

    try:
        # Read the Excel file into a pandas DataFrame
        all_sheets = pd.read_excel(excel_file, sheet_name=sheet_name)
        logging.info(
            f"Successfully loaded Excel file '{excel_file}' from sheet '{sheet_name}'.")

        # The pd.read_excel(excel_file, sheet_name=None) function reads all sheets into a dictionary of DataFrames.
        # The keys of the dictionary are sheet names, and the values are DataFrames containing the data from each sheet.

        # Limitation:
        #   We asume only one sheet
        #   Get the first sheet
        # Get the name of the first sheet
        first_sheet_name = list(all_sheets.keys())[0]
        # Get the DataFrame for the first sheet
        first_df = all_sheets[first_sheet_name]

        return first_df

    except FileNotFoundError:
        logging.error(f"Error: The file '{excel_file}' does not exist.")
    except pd.errors.ExcelFileNotFoundError:
        logging.error(
            f"Error: The file '{excel_file}' is not a valid Excel file.")
    except pd.errors.EmptyDataError:
        logging.error(
            f"Error: The file '{excel_file}' is empty or unreadable.")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")

    return None


def save_to_excel(df, output_file):
    # Convert the data (list of dictionaries) into a pandas DataFrame
    # df = pd.DataFrame(data)

    # Save the DataFrame to an Excel file
    # index=False to avoid saving row indices
    df.to_excel(output_file, index=False)


def process_summaries_and_save_excel(df, output_file, summaries):

    # Load the Excel file using openpyxl
    wb = openpyxl.load_workbook(output_file)

    for i, summary in enumerate(summaries):

        # Create a new sheet for charts
        ws_data = wb.create_sheet(title="Grouped Data " + str(i + 1))

        if 'filter' in summary:
            # Apply the operator dynamically to the DataFrame column
            filter = summary['filter']
            df = df[OPS[filter['operator']](
                df[filter['column']], filter['value'])]

        # Row position in the Charts sheet to insert the next chart
        row_position = 1

        if len(summary['groupby']) == 1:

            # Count occurrences of each item level
            counts = df[summary['groupby'][0]].value_counts()
            percentages = (counts / counts.sum()) * 100

            # Write the data to the worksheet
            ws_data.append([summary['groupby'][0], "Count", "Percentage"])
            for key, count in counts.items():
                percentage = percentages[key]
                ws_data.append([key, count, percentage])

            # Create chart
            chart = PieChart()
            chart.style = 2
            chart.title = summary['title']

            # Add data to the chart
            data = Reference(ws_data, min_col=3, min_row=1,
                             max_col=3, max_row=len(percentages)+1)
            labels = Reference(ws_data, min_col=1, min_row=2,
                               max_row=len(percentages)+1)
            chart.add_data(data, titles_from_data=True)
            chart.set_categories(labels)

            chart.add_data(data, titles_from_data=True)
            chart.set_categories(labels)

            # Add the chart to the worksheet
            ws_data.add_chart(chart, "D5")

        elif len(summary['groupby']) == 2:

            # Group data
            grouped = df.groupby(
                summary['groupby']).size().unstack(fill_value=0)

            # Write the DataFrame to the 'Grouped Data' sheet
            for r in dataframe_to_rows(grouped, index=True, header=True):
                ws_data.append(r)

            # Loop through each subgroup to create a pie chart
            for i, subgroup in enumerate(grouped.index, start=3):

                # Create chart
                chart = PieChart()
                chart.style = 2
                chart.title = ("%s for %s" % (
                    str(summary['title']), str(subgroup)))

                # Define the data and labels for the chart
                data_ref = Reference(ws_data, min_col=2, min_row=i, max_col=len(
                    grouped.columns) + 1, max_row=i)
                labels_ref = Reference(ws_data, min_col=2, min_row=1, max_col=len(
                    grouped.columns) + 1, max_row=1)

                chart.add_data(data_ref, titles_from_data=True)
                chart.set_categories(labels_ref)

                # Add the chart to the Charts sheet
                ws_data.add_chart(chart, f'O{row_position}')

                # Adjust row position for the next chart
                row_position += 15

        else:
            logging.error(
                "Maximum supported grouping is 2. %d was given" % len(summary['groupby']))

    # Save the workbook
    wb.save(output_file)

    logging.info(f"Excel file with pie charts saved as {output_file}")


def save_to_csv(df, output_file):
    df.to_csv(output_file,
              index=False,  # Do not write row indices
              date_format='%Y-%m-%d',  # Format for date columns
              float_format='%.2f')  # Format for float columns


def load_csv_file(csv_file):
    try:
        # Handle encoding errors by replacing problematic characters with a placeholder
        df = pd.read_csv(csv_file, encoding='utf-8')
        logging.debug(
            "Successfully loaded CSV with UTF-8 encoding and error handling.")

    except UnicodeDecodeError:
        logging.debug("UTF-8 encoding failed, trying 'latin1' encoding...")

        # Try reading with 'latin1' encoding if UTF-8 fails
        try:
            df = pd.read_csv(csv_file, encoding='latin1')
            logging.debug(
                "Successfully loaded CSV with latin1 encoding and error handling.")
        except Exception as e:
            logging.error(f"Failed to load CSV: {e}")
            return None

    logging.info("File successfully loaded: %s" % csv_file)

    return df


def save_json(json_data, output_file):
    # Save the JSON string to a file
    with open(output_file, mode='w', encoding="utf-8") as f:
        f.write(json_data)


def load_yaml(yaml_file):
    # Open and load the YAML file
    try:
        with open(yaml_file, 'r') as file:
            data = yaml.safe_load(file)
            return data
    except FileNotFoundError:
        logging.error(f"Error: The file '{yaml_file}' was not found.")
        sys.exit(1)
    except yaml.YAMLError as exc:
        logging.error(f"Error parsing YAML file: {exc}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        sys.exit(1)


def random_string():

    ran = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

    return ran


def change_control(column_name, transformed_columns):
    if column_name not in transformed_columns:
        transformed_columns[column_name] = 1
    else:
        transformed_columns[column_name] += 1

    return transformed_columns


def apply_condition(row, column_name, destination_column_name, conditions):

    for c in conditions:
        if 'if_value' in c and c['if_value'] == row[column_name]:
            return c['set']
        if 'else' in c:
            return c['else']

    return row[destination_column_name]


def main():

    global logging
    global cfg

    # Get params

    (file, options) = parse_arguments(sys.argv[1:])

    # Logger

    logging.basicConfig(level=getattr(logging, options.log_level.upper()),
                        format='%(asctime)s - %(levelname)s - %(message)s')
    logging.info("Welcome to tranXformation")

    # Get DetectBoX configuration

    cfg = load_yaml(options.config_file)

    # Load data

    df = None

    if options.format.lower() == 'excel':
        # Convert Excel to JSON
        df = load_excel_file(file)
    else:
        # Convert CSV to JSON
        df = load_csv_file(file)

    if isinstance(df, pd.DataFrame):
        # Successfully loaded
        logging.debug("Sample data:")
        logging.debug(df.head(10))  # Print the first rows
    else:
        logging.error("Data is not a DataFrame.")

    # Apply operations

    transformed_columns = {}
    suffix = '_tranXformation_orig'

    tranformatations = cfg['tranformatations']

    for tr in tranformatations:

        logging.info("Processing transformation for column '%s' and operation '%s'" % (
            tr['column'], tr['operation']))

        try:

            column_name = tr['column']

            # Copy. Keep orignal values before transforamtion. Count transformations.

            transformed_columns = change_control(
                column_name, transformed_columns)

            if tr['operation'].lower() != 'create_column' and transformed_columns[column_name] == 1:
                # Create a copy before the fist transformation
                df[column_name + suffix] = df[column_name]

            if tr['operation'].lower() == 'explode_into_rows':
                # Explode columns
                logging.info("Explode in rows '%s' column by separator '%s'" % (
                    column_name, tr['separator']))
                df[column_name] = df[column_name].str.split(tr['separator'])
                df = df.explode(column_name)
                df[column_name] = df[column_name].astype(str)
                df[column_name] = df[column_name].str.strip()
                logging.debug(df.head(10))

            elif tr['operation'].lower() == 'split_into_columns':
                # Split and complete into columns
                if 'pattern' in tr:
                    # separator an pattern are equivalent
                    tr['separator'] = tr['pattern']

                logging.info("Split column '%s' into columns %s by separator or pattern '%s'" % (
                    column_name, tr['destination_columns'], tr['separator']))

                regex = False
                if 'regex' in tr:
                    regex = tr['regex']

                n = None
                if 'num_splits' in tr:
                    n = tr['num_splits']

                aux = df[column_name].str.split(
                    tr['separator'], n=n, regex=regex, expand=True)

                for c in tr['destination_columns']:
                    df[c] = None

                for i, c in enumerate(tr['destination_columns']):
                    if i in aux:
                        df[c] = aux[i]

                df[column_name] = df[column_name].astype(str)
                df[column_name] = df[column_name].str.strip()

            elif tr['operation'].lower() == 'conditional_tagging':
                # Check if the column exists and create if needed
                if tr['destination_column'] not in df.columns:
                    df[tr['destination_column']] = ''
                # Apply the function to the column_name column and assign the result to a new column
                # df[tr['destination_column']] = df[column_name].apply(assign_value, args=(tr['conditions'],))
                df[tr['destination_column']] = df.apply(lambda row: apply_condition(
                    row, column_name, tr['destination_column'], tr['conditions']), axis=1)

            elif tr['operation'].lower() == 'rename_column':
                # Rename specific columns
                df = df.rename(
                    columns={column_name: tr['renamed_column_name']})

            elif tr['operation'].lower() == 'delete_column':
                # Delete specific columns
                df = df.drop(columns=[column_name])

            elif tr['operation'].lower() == 'create_column':
                # Create a new column and fill with random strings if defined
                df[column_name] = None
                if tr['generate_random']:
                    df[column_name] = [random_string() for _ in range(len(df))]

            else:
                logging.error("Unknown operation: %s", tr['operation'])

        except KeyError as e:
            print(
                f"KeyError: The key '{e.args[0]}' is missing in the configuration: %s" % tr)

    # Save data

    output_file = options.output_filename

    if options.format.lower() == 'excel':
        # Save DataFrame to Excel file
        if not output_file.endswith('.xlsx'):
            output_file += '.xlsx'
        # Save and finish
        save_to_excel(df, output_file)

        if 'summaries' in cfg and len(cfg['summaries']) > 0:
            # Crate processed summaries
            process_summaries_and_save_excel(df, output_file, cfg['summaries'])

    else:
        # Save DataFrame to CSV with specific formatting
        if not output_file.endswith('.csv'):
            output_file += '.csv'
        save_to_csv(df, output_file)

    logging.info("Saving transformation result to: %s" % output_file)

    # Print summary

    print("\nTranXformations:\n")
    if len(transformed_columns) == 0:
        print(" - Nothing transformed.")
    else:
        for key, value in transformed_columns.items():
            print(" - Column: %s:\t\t%d transformations" % (key, value))

    if 'summaries' in cfg and len(cfg['summaries']) > 0:
        print("\n\nSummaries:\n")
        for s in cfg['summaries']:
            print(" - %s" % s['title'])

    # print("\nSample (10 lines):\n")
    # print(df.head(10))
    print()


if __name__ == "__main__":
    main()
