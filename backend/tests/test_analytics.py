import pytest

from app.services.analytics import validate_sql


def test_validate_sql_adds_limit():
    assert validate_sql("SELECT product FROM sales").lower().endswith("limit 100")


@pytest.mark.parametrize("sql", ["DELETE FROM sales", "DROP TABLE sales", "UPDATE sales SET revenue = 0"])
def test_validate_sql_blocks_mutations(sql):
    with pytest.raises(ValueError):
        validate_sql(sql)


def test_validate_sql_blocks_sensitive_columns():
    with pytest.raises(ValueError):
        validate_sql("SELECT email FROM customers LIMIT 5")
