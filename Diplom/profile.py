from httpreq import VKHttpWorker, ODNHttpWorker, InstaHttpWorker


class UserProfile:
    def __init__(self, user_id):
        self.user_id = user_id
        self.albums_list = []
        self.requester = None

    def get_albums(self, count=None):
        photos_count, albums = self.requester.get_albums(self.user_id, count)
        return {self.user_id: albums,
                'photos_count': photos_count
                }

    def get_init_status(self):
        return self.requester.get_status()


class VKProfile(UserProfile):
    def __init__(self, user_id):
        super().__init__(user_id)
        self.requester = VKHttpWorker()


class ODNProfile(UserProfile):
    def __init__(self, user_id):
        super().__init__(user_id)
        self.requester = ODNHttpWorker()


class InstaProfile(UserProfile):

    def __init__(self, user_id):
        super().__init__(user_id)
        self.requester = InstaHttpWorker()