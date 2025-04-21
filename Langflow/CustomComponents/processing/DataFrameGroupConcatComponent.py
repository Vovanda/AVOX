from langflow.custom import Component
from langflow.io import StrInput, Output, DataFrameInput, IntInput, DictInput, MessageTextInput
from langflow.schema import DataFrame, Data
import pandas as pd
from typing import List


class DataFrameGroupConcatComponent(Component):
    display_name = "DataFrame Group & Concat"
    description = "Group and concatenate DataFrame columns with dynamic patterns"
    icon = "Table"
    category = "Data Processing"
    MAX_COLUMNS = 10

    inputs = [
        DataFrameInput(name="input_df", display_name="Input DataFrame", required=True),
        StrInput(name="group_by_columns", display_name="Group By Columns", required=True, value="source"),
        StrInput(name="concat_columns", display_name="Concat Columns", required=False),
        IntInput(
            name="num_concat_columns",
            display_name="Number of Concat Columns",
            required=True,
            value=0,
            range_spec={"min": 0, "max": MAX_COLUMNS, "step": 1},
            real_time_refresh=True,
        ),
        MessageTextInput(
            name="default_concat_rule",
            display_name="Default Concat Rule",
            required=False,
            value="%newLine%",
        ),
    ]

    outputs = [
        Output(display_name="Grouped DataFrame", name="grouped_df", method="get_grouped_df"),
        Output(display_name="Grouped Data", name="grouped_data", method="get_grouped_data"),
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.processed_df = pd.DataFrame()
        self.data_objects = []

    def update_build_config(self, build_config, field_value, field_name=None):
        if field_name == "num_concat_columns":
            try:
                field_value_int = int(field_value)
            except ValueError:
                return build_config

            existing_fields = {key: build_config.pop(key) for key in list(build_config.keys()) if key.startswith("concat_rule_and_name_")}

            for i in range(1, field_value_int + 1):
                key = f"concat_rule_and_name_{i}"
                column_display_name = self._get_column_name(i)

                if key in existing_fields:
                    build_config[key] = existing_fields[key]
                else:
                    build_config[key] = DictInput(
                        display_name=f"Concat Rule & New Name for '{column_display_name}'",
                        name=key,
                        info=f"First input: concatenation rule for '{column_display_name}' (You can create a specific template using: %value%, %id%, {{columnName}} placeholders).\n Second input: new column name for '{column_display_name}'.",
                        input_types=["Message", "Message"],
                    ).to_dict()
            
            build_config["num_concat_columns"]["value"] = field_value_int
        return build_config

    def build(self) -> None:
        self.process_data()

    def process_data(self):
        try:
            df = self._get_input_df()
            group_cols = self._parse_columns(self.group_by_columns)
            concat_rules = []
            new_column_names = []
            
            for i in range(1, self.num_concat_columns + 1):
                key = f"concat_rule_and_name_{i}"
                rule, new_name = self._get_concat_rule_and_name(key)
                concat_rules.append(rule)
                new_column_names.append(new_name)

            self._process_dataframe(df, group_cols, concat_rules, new_column_names)
            self._generate_outputs(group_cols, new_column_names)
        except Exception as e:
            self.status = str(e)
            self.log(f"Error: {e}")
            raise

    def get_grouped_df(self) -> DataFrame:
        self.process_data()
        return DataFrame(data=self.processed_df.to_dict("records")) if not self.processed_df.empty else None

    def get_grouped_data(self) -> List[Data]:
        self.process_data()
        return self.data_objects

    def _get_input_df(self) -> pd.DataFrame:
        if not self.input_df:
            raise ValueError("Input DataFrame is required")
        return pd.DataFrame([item.data for item in self.input_df.to_data_list()])

    def _parse_columns(self, columns: str) -> List[str]:
        return [col.strip() for col in columns.split(",") if col.strip()]

    def _get_column_name(self, index: int) -> str:
        columns = self._parse_columns(self.concat_columns)
        return columns[index - 1] if index <= len(columns) else f"Column {index}"

    def _get_concat_rule_and_name(self, key: str):
        value = getattr(self, key, {})
        rule = value.get("Message_1", "") or self.default_concat_rule or "%newLine%"
        new_name = value.get("Message_2", "")
        return rule, new_name

    def _process_dataframe(self, df: pd.DataFrame, group_cols: List[str], concat_rules: List[str], new_column_names: List[str]):
        agg_rules = {}
        for col, rule, new_name in zip(self._parse_columns(self.concat_columns), concat_rules, new_column_names):
            agg_rules[col] = lambda x, pattern=rule: self._format_series(x, pattern, df)
        self.processed_df = df.groupby(group_cols, as_index=False).agg(agg_rules)
        self.processed_df.rename(columns=dict(zip(self._parse_columns(self.concat_columns), new_column_names)), inplace=True)

    def _format_series(self, series: pd.Series, pattern: str, df: pd.DataFrame) -> str:
        elements = []
        pattern = pattern.replace('%newLine%', '\n').replace('%tab%', '    ')
        is_separator = not any(placeholder in pattern for placeholder in ['%value%', '%id%', '{column_name}'])

        if is_separator:
            return pattern.join(str(val) for val in series.dropna())
        
        for i, val in enumerate(series.dropna()):
            formatted_value = pattern.replace('%value%', str(val)).replace('%id%', str(i + 1))
            for col in df.columns:
                value_to_replace = str(df[col].iloc[i]).strip() or 'N/A'
                formatted_value = formatted_value.replace(f'{{{col}}}', value_to_replace)
            elements.append(formatted_value)
        
        return ''.join(elements)

    def _generate_outputs(self, group_cols: List[str], new_column_names: List[str]):
        self.data_objects = [
            Data(
                text=" | ".join(str(row[col]) for col in group_cols),
                data=row.to_dict()
            )
            for _, row in self.processed_df.iterrows()
        ]
