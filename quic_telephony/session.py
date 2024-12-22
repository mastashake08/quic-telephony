class SessionManager:
    def __init__(self):
        self.session_store = {}

    def save_session(self, session_ticket, user_id):
        self.session_store[session_ticket] = user_id

    def get_user_id(self, session_ticket):
        return self.session_store.get(session_ticket)
