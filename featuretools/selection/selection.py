def remove_low_information_features(feature_matrix, features=None):
    """Select features that have at least 2 unique values and that are not all null

        Args:
            feature_matrix (:class:`pd.DataFrame`): DataFrame whose columns are feature names and rows are instances
            features (list[:class:`featuretools.FeatureBase`] or list[str], optional): List of features to select

        Returns:
            (feature_matrix, features)

    """
    keep = [c for c in feature_matrix
            if (feature_matrix[c].nunique(dropna=False) > 1 and
                feature_matrix[c].dropna().shape[0] > 0)]
    feature_matrix = feature_matrix[keep]
    if features is not None:
        features = [f for f in features
                    if f.get_name() in feature_matrix.columns]
        return feature_matrix, features
    return feature_matrix


'''
The three functions below use logic from EvalML DataChecks
'''


def find_highly_null_features(feature_matrix, pct_null_threshold=0.95):
    """
    Determine features from a feature matrix that have higher than a set threshold
    of null values.

    Args:
        feature_matrix (:class:`pd.DataFrame`): DataFrame whose columns are feature names and rows are instances
        pct_null_threshold (float): If the percentage of NaN values in an input feature exceeds this amount,
                that feature will be considered highly-null. Defaults to 0.95.

    Returns:
        List of featxure names that will match columns in the inputted feature matrix
        where the null percentage was above the set threshold

    """
    if pct_null_threshold < 0 or pct_null_threshold > 1:
        raise ValueError("pct_null_threshold must be a float between 0 and 1, inclusive.")

    percent_null_by_col = (feature_matrix.isnull().mean()).to_dict()
    # -->maybe split into two cases for strictly > for 0 and >= for nonzero
    return [f_name for f_name, pct_null in percent_null_by_col.items() if pct_null > pct_null_threshold]


def find_single_value_features(feature_matrix, count_nan_as_value=False):
    """
    Determines columns in feature matrix where all the values are the same.

    Args:
        feature_matrix (:class:`pd.DataFrame`): DataFrame whose columns are feature names and rows are instances
        count_nan_as_value (bool): If True, missing values will be counted as their own unique value.
                    If set to True, a feature that has one unique value and all other data is missing will be
                    counted as only having a single unique value. Defaults to False.

    Returns:
        List of feature names of all the single value features - note None is not counted
        as a value, so "single value" is either 0 or 1 unique values
    """
    unique_counts_by_col = feature_matrix.nunique(dropna=not count_nan_as_value).to_dict()
    return [f_name for f_name, unique_count in unique_counts_by_col.items() if unique_count <= 1]


def find_highly_correlated_features(feature_matrix, pct_corr_threshold=0.95, features_to_check=None, features_to_exclude=None):
    """
    Determines whether any pairs of features are highly correlated with one another.

    Args:
        feature_matrix (:class:`pd.DataFrame`): DataFrame whose columns are feature names and rows are instances
        pct_corr_threshold (float): The correlation threshold to be considered highly correlated. Defaults to 0.95.
        cols_to_check (set{str}, optional): Set of column names to check whether any pairs are highly correlated.
                    If null, defaults to checking all columns.
        cols_to_exclude set[str], optional): Set of colum names to not check correlation between.
                    If null, will not exclude any columns.

    Returns:
        list[tuple(str, str)] of column pairs that is correlated above the set threshold.
    """
    if pct_corr_threshold < 0 or pct_corr_threshold > 1:
        raise ValueError("pct_corr_threshold must be a float between 0 and 1, inclusive.")

    if features_to_check is None:
        features_to_check = set(feature_matrix.columns)

    # -->maybe also do check for if col is actually in fm/is actually of correct dtype
    if features_to_exclude is not None:
        features_to_check = {col for col in features_to_check if col not in features_to_exclude}

    numeric_dtypes = ['int16', 'int32', 'int64', 'float16', 'float32', 'float64']
    boolean = ['bool']
    numeric_and_boolean_dtypes = numeric_dtypes + boolean

    fm_to_check = (feature_matrix[list(features_to_check)]).select_dtypes(include=numeric_and_boolean_dtypes)

    highly_correlated_by_pairs = {}
    for f_name1, col1 in fm_to_check.iteritems():
        for f_name2, col2 in fm_to_check.iteritems():
            pair = tuple(sorted((f_name1, f_name2)))
            if f_name1 == f_name2 or pair in highly_correlated_by_pairs:
                continue

            highly_correlated_by_pairs[pair] = abs(col1.corr(col2))

    return [f_pair for f_pair, correlation in highly_correlated_by_pairs.items() if correlation >= pct_corr_threshold]
