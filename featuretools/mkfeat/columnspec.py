import pandas as pd

from .error import Error


_mkfeat_typestr_to_converter = {
    "number": pd.to_numeric,
    "date": pd.to_datetime
}

_mkfeat_typestr_to_dtype = {
    "bool": bool
}


class ColumnSpec:
    """
    컬럼명이나 유형과 관련된 정보를 처리하는 목적의 클래스. 현재는 컬럼명에 대한 정보를 처리하는 기능만 구현됨
    """
    def __init__(self, columns):
        self.columns = columns
        self._auto_keyname = None

    def validate(self):
        """
        Column 정의에 대한 검증. 모든 컬럼에 name, type이 정의되어 있는지, key가 전체 컬럼에 1개 정의, label이 정의된 컬럼이 1개
        혹은 정의되지 않았는지를 확인함
        Returns:
            :class:.Error: column 정의가 문제 없는 경우 OK반환. 그렇지 않으면 해당하는 오류값 반환.
        """
        has_key = False
        has_label = False
        for colinfo in self.columns:
            if 'name' not in colinfo or 'type' not in colinfo:
                return Error.ERR_COLUMN_HAS_NO_NAME_OR_TYPE
            if 'key' in colinfo:
                if colinfo['key']:
                    if has_key:
                        return Error.ERR_COLUMN_MULTI_KEY
                    if 'label' in colinfo and colinfo['label']:
                        return Error.ERR_COLUMN_KEY_AND_LABEL
                    has_key = True
            if 'label' in colinfo:
                if colinfo['label']:
                    if has_label:
                        return Error.ERR_COLUMN_MULTI_LABEL
                    has_label = True
        return Error.OK

    def get_colnames(self):
        """
        컬럼명 배열을 반환. pandas의 read_csv() 함수 전달 인자를 쉽게 생성하기 위함

        Returns:
            컬럼명으로 구성된 배열
        """
        colnames = []
        for colinfo in self.columns:
            colnames.append(colinfo['name'])
        return colnames

    def get_usecols(self, numeric_only: bool = False, label_only: bool = False, exclude_skip: bool = False):
        """
        컬럼명 배열을 반환. pandas의 read_csv()의 usecols 파라미터 전달용 함수

        Args:
            numeric_only (bool): True의 경우, numeric 형식으로 가능한 column명 만을 추출
            label_only (bool): True의 경우 label에 대한 column명 만을 추출
            exclude_skip (bool): True의 경우 label, train, bypass 컬럼을 제거하여 column명 목록 생성
        Returns:
            컬럼명으로 구성된 배열
        """
        colnames = []
        for colinfo in self.columns:
            if numeric_only and not self._is_numeric_type(colinfo['type']):
                continue
            if label_only and ('label' not in colinfo or not colinfo['label']):
                continue
            if exclude_skip and (('label' in colinfo and colinfo['label']) or
                                 ('train' in colinfo and colinfo['train']) or
                                 ('bypass' in colinfo and colinfo['bypass'])):
                continue
            colnames.append(colinfo['name'])
        return colnames

    def get_dtypes(self):
        dtypes = {}
        for colinfo in self.columns:
            dtype = self._get_dtype_from_strtype(colinfo['type'])
            if dtype is not None:
                dtypes[colinfo['name']] = dtype
        return dtypes

    def get_converters(self):
        converters = {}
        for colinfo in self.columns:
            converter = self._get_converter_from_strtype(colinfo['type'])
            if converter is not None:
                converters[colinfo['name']] = converter
        return converters

    def get_key_colname(self):
        """
        Get key column name. If no key is specified, key is automatically generated.

        Returns:
            key column name which can be used as row identifer.
        """
        for colinfo in self.columns:
            if 'key' in colinfo and colinfo['key']:
                return colinfo['name']
        self._setup_auto_keyname()
        return self._auto_keyname

    def is_auto_keyname(self):
        return True if self._auto_keyname else False

    def get_label_colname(self):
        for colinfo in self.columns:
            if 'label' in colinfo and colinfo['label']:
                return colinfo['name']
        return None

    def get_train_colname(self):
        for colinfo in self.columns:
            if 'train' in colinfo and colinfo['train']:
                return colinfo['name']
        return None

    def get_bypass_colnames(self):
        colnames = []
        for colinfo in self.columns:
            if 'bypass' in colinfo and colinfo['bypass']:
                colnames.append(colinfo['name'])
        return colnames

    def get_is_numerics(self):
        """
        importance 결과 구성을 위하여 numeric 컬럼 여부 배열을 추출
        Returns:

        """
        is_numerics = []
        for colinfo in self.columns:
            if 'label' in colinfo and colinfo['label'] or 'bypass' in colinfo and colinfo['bypass']:
                is_numerics.append(False)
            else:
                is_numerics.append(self._is_numeric_type(colinfo['type']))
        return is_numerics

    @staticmethod
    def _get_dtype_from_strtype(typestr):
        if typestr in _mkfeat_typestr_to_dtype:
            return _mkfeat_typestr_to_dtype[typestr]
        return None

    @staticmethod
    def _get_converter_from_strtype(typestr):
        if typestr in _mkfeat_typestr_to_converter:
            return _mkfeat_typestr_to_converter[typestr]
        return None

    @staticmethod
    def _is_numeric_type(self):
        return self in ('number', 'bool')

    def _setup_auto_keyname(self):
        if self._auto_keyname:
            return
        colnames = self.get_colnames()
        if 'id' not in colnames:
            keyname = 'id'
        else:
            for i in range(1, 100000):
                keyname = "id_{}".format(i)
                if keyname not in colnames:
                    break
        self._auto_keyname = keyname
