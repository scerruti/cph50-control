import os
from chargepoint_dal import ChargePointDAL

def test_session_details():
    username = os.getenv("CP_USERNAME")
    password = os.getenv("CP_PASSWORD")
    station_id = os.getenv("CP_STATION_ID")
    session_id = 4751613101
    dal = ChargePointDAL(username, password, station_id)
    activity = dal.get_session_activity(session_id)
    print("Session activity for", session_id)
    print(activity)

if __name__ == "__main__":
    test_session_details()
