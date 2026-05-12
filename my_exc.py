class NoData(Exception):
    """ Raised when there is no data in DB for specified parameters (currently only parameter is: date) """
    def __init__(self, str_date: str):
        super().__init__(f'No data in DB for date={str_date}')
        self.str_date = str_date
