# Simple tests for our project. pytest runs every function that starts with "test_".
import py_compile
import pandas as pd

MACROS = ["Protein(g)", "Carbs(g)", "Fat(g)"]


def load_clean_data():
    df = pd.read_csv("All_Diets.csv")
    # fill missing numbers with the column average (numbers only)
    df[MACROS] = df[MACROS].fillna(df[MACROS].mean())
    return df


def test_csv_has_needed_columns():
    df = pd.read_csv("All_Diets.csv")
    for col in ["Diet_type", "Recipe_name", "Cuisine_type"] + MACROS:
        assert col in df.columns


def test_no_missing_values_after_cleaning():
    df = load_clean_data()
    assert df[MACROS].isnull().sum().sum() == 0


def test_average_macros_per_diet():
    df = load_clean_data()
    avg = df.groupby("Diet_type")[MACROS].mean()
    assert len(avg) > 0              # at least one diet type
    assert (avg >= 0).all().all()    # averages are never negative


def test_python_files_have_no_syntax_errors():
    py_compile.compile("data_analysis.py", doraise=True)
