# Imports libraries.
import pandas as pd

# Creates a class with the agent's toolkit to analyze deviations.
class AgentToolkit:

    '''
    ---A toolkit for analyzing deviations (week-on-week and year-on-year) in a dataset.
    ---Ensures that the data is validated, corrected, completed, and sorted before calculating deltas.
    ---Avoids the agent from calculating deviations itself, it only has to focus on the 'vs_' columns.
    '''

    # Initializes class
    def __init__(
        self,
        df: pd.DataFrame,
        date_col: str,
        value_col: str,
        *groups_cols: tuple[str, ...],
        ):
        
        '''
        Args:
            df (pd.DataFrame): The input dataset.
            date_col (str): The name of the column containing dates in 'YYYY-WW' format (e.g. 'yearweek').
            value_col (str): The name of the column containing numeric values to analyze (e.g. 'searchers').
            groups_cols (str): The names of one or more columns containing groups identifiers (e.g. 'countries' and 'products').
        '''

        # Copies the dataframe and corrects column names and inputs.
        self.df = df.copy()
        self.df.columns = self.df.columns.str.lower()
        self.date_col = date_col.lower()
        self.value_col = value_col.lower()
        self.groups_cols = [x.lower() for x in groups_cols]

        # Runs process.
        self._process()

    def _process(self):
        # If all inputs exist
        if self.validate_existence() == True:
            # Runs functions.
            self.correct_datetime()
            self.correct_numeric()
            # self.sort_df()
            self.complete_df()
            self.create_yw()
            self.create_4w()
            self.create_deltas()
        else:
            # Raises something.
            raise ValueError('Required columns are missing from the DataFrame.')

    def validate_existence(self):
        # Creates sets of columns.
        cols = set([self.date_col, self.value_col] + self.groups_cols)
        df_cols = set(self.df.columns.values)

        # Checks if input columns are in dataframe columns.
        if cols.issubset(df_cols):
            return True
        else:
            return False

    def correct_datetime(self):
        # Corrects format of datetime column, taking into account 'YYYY-WW' format.
        self.df[self.date_col] = pd.to_datetime(self.df[self.date_col] + '-1', format='%G-%V-%u')

    def correct_numeric(self):
        # Corrects format of numeric values, taking into account spanish decimals.
        self.df[self.value_col] = pd.to_numeric(self.df[self.value_col].astype(str).str.replace(',', '.'))

    # def sort_df(self):
    #     # Sorts dataframe by date and grouping columns
    #     self.df = self.df.sort_values([self.date_col, self.groups_cols])

    def complete_df(self):
        # Calculates range of weekly observations.
        min_date = self.df[self.date_col].min()
        max_date = self.df[self.date_col].max()
        dates = pd.date_range(start=min_date, end=max_date, freq='W-MON')

        # Calculates unique values of grouping columns.
        groups = [self.df[x].unique() for x in self.groups_cols]

        # Create a complete dataframe, using a multiindex with dates and groups.
        complete_index = pd.MultiIndex.from_product([dates] + groups, names=[self.date_col] + self.groups_cols)
        complete_df = pd.DataFrame(index=complete_index).reset_index()

        # Left-joins with the original dataframe to fill the observed values.
        self.df = pd.merge(complete_df, self.df, on=[self.date_col] + self.groups_cols, how='left')

    def create_yw(self):
        # Creates columns with year and week numbers.
        self.df['year'] = self.df[self.date_col].dt.isocalendar().year
        self.df['weeknum'] = self.df[self.date_col].dt.isocalendar().week

    def create_4w(self):
        # Creates moving average of lenght 4
        self.df['{} 4w'.format(self.value_col)] = self.df.groupby(self.groups_cols)[self.value_col].transform(lambda x: x.rolling(4, 4).mean())

    def create_deltas(self):
        # Creates deviations from the sorted complete dataframe.
        self.df['vs_lw'] = self.df.groupby(self.groups_cols)[self.value_col].pct_change(fill_method=None)
        self.df['vs_l4w'] = self.df.groupby(self.groups_cols)['{} 4w'.format(self.value_col)].pct_change(fill_method=None)
        self.df['vs_ly'] = self.df.groupby(self.groups_cols + ['weeknum'])[self.value_col].pct_change(fill_method=None)