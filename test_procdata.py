import pytest
from procdata import process_data

def test_emptydata():
    with pytest.raises(ValueError):
        process_data(data=None)
    with pytest.raises(ValueError):
        process_data(data=123)

    process_data(data={})
