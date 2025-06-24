import unittest
from libs.taskModel import TaskModel
from libs.imageProcessing import ImageProcessing
from libs.atlasSensor import AtlasSensor
from libs.lidar import Lidar

class TestTaskModel(unittest.TestCase):
    def setUp(self):
        # Create an instance of TaskModel
        mock_imageProcessing = ImageProcessing()
        mock_atlasSensor = AtlasSensor()
        mock_lidar = Lidar()
        self.task_model = TaskModel(mock_imageProcessing, mock_atlasSensor, mock_lidar)

    def tearDown(self):
        # Clean up any resources used for testing
        pass

    def test_provideSemiStructuredData(self):

        # Call the method you want to test
        result = self.task_model.provideSemiStructuredData()

        # Print output of interest ...
        print(result)

        # Perform assertions to verify the result
        self.assertIsInstance(result, str)
        self.assertEqual(result, r'{"imageProcessing":{"_cap":null,"_colorCAM":"red","_intervalbild":5,"_imgB":60,"_imgC":30,"_imgS":30,"_camCalib":false,"_successINIT":false,"_frame":null,"_fmt":null,"_images":[],"_imagenames":[]},"atlasSensor":{"_device":null,"_times_list":{},"_modules_list":[],"_colorpH":"red","_colorT":"red","_colorCond":"red","_colorOR":"red","_device_list":[]},"lidar":{"_ser":null,"_showLIDAR":false,"_colorLIDAR":"red","_pulplevel":"-"},"hasbeeped":0,"nconc":null,"status":"PAUSED","t1":0,"t2":0,"flotationtime":0,"t1flot":0,"t2flot":0,"currentstage":0,"currentstagetype":"","currentstagename":"","workingfolder":"D:\\Users\\Christian\\Documents\\Arbeit\\HZDR\\digifloatREPO","samplefolder":null,"samplenames":null,"scheme":[{"Stage":"","Time(s)":"","Type":"Conditioning"},{"Stage":"","Time(s)":"","Type":"Flotation"}],"schemesample":[{"Air flow rate":"","Rotor speed":"","Target pH":"4","Reagent":"","Concentration":"","Volume":"","Stage":""},{"Air flow rate":"","Rotor speed":"","Target pH":"4","Reagent":"","Concentration":"","Volume":"","Stage":""}],"nstages":1,"targett":"","times_list_live":{}}')

if __name__ == '__main__':
    unittest.main()