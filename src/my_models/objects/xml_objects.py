from robosuite.models.objects import MujocoXMLObject

class TorsoObject(MujocoXMLObject):
    """
    Torso object
    """

    def __init__(self):
        super().__init__("my_models/assets/objects/human_torso.xml")