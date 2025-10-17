from PyQt5.QtWidgets import (QTabWidget, QApplication, QMainWindow)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import (QGuiApplication,QColor)
import logging
import pathlib
import sys
from importlib.metadata import version, PackageNotFoundError

try:
    #Run from within a package - '.' references to this package => relative import
    from .libs.controller import Controller
    ##Viewers
    from .libs.tabViewSetup import TabViewSetup
    from .libs.tabViewRun import TabViewRun
    from .libs.tabViewInformation import TabViewInformation
    from .libs.tabViewRestartExit import TabViewRestartExit
    from .libs.tabViewCalibLidar import TabViewCalibLidar    
    from .libs.tabViewCalibSensors import TabViewCalibSensors    
    from .libs.tabViewBronkhorstFlowControl import TabViewBronkhorstFlowControl    
    # from .libs.tabViewSEWControl import TabViewSEWControl # disabled since it is giving problems    
    ##Hardware Inferface Classes
    from .libs.atlasSensor import AtlasSensor
    from .libs.lidar import Lidar
    from .libs.bronkhorstFlowControlModel import BronkhorstFlowControlModel    
    # from .libs.SEWcontrolModel import SEWcontrolModel    # disabled since it is giving problems  
    #Wrapper for AtlasSensor
    from .libs.atlasSensorWrapper import AtlasSensorWrapper    
    ##Model
    from .libs.taskModel import TaskModel
    from .libs import eventManager
    #Camera Adapter Class
    from .libs.camAdapter import CamAdapter  
    ##Interface to offline image acquisition
    from .libs.imageStorage import ImageStorage
    ##Interface to Data Lake
    from .libs.dataForwarder import DataForwarder
    ##Drop down menu
    from .libs.dropDownMenu import DropDownMenu    
    ##EventManager
    from .libs import eventManager      
    ##ConfigurationManager
    from .libs import configurationManager
    ## pop-up windows of the main window
    from .libs.enterProjectWindow import EnterProjectWindow
except:
    #Run as a script in standalone mode ... no package context => absolute import
    from libs.controller import Controller
    ##Viewers
    from libs.tabViewSetup import TabViewSetup
    from libs.tabViewRun import TabViewRun
    from libs.tabViewInformation import TabViewInformation
    from libs.tabViewRestartExit import TabViewRestartExit
    from libs.tabViewCalibLidar import TabViewCalibLidar
    from libs.tabViewCalibSensors import TabViewCalibSensors
    from libs.tabViewBronkhorstFlowControl import TabViewBronkhorstFlowControl   
    # from libs.tabViewSEWControl import TabViewSEWControl     # disabled since it is giving problems      
    ##Hardware Inferface Classes
    from libs.atlasSensor import AtlasSensor
    from libs.lidar import Lidar
    from libs.bronkhorstFlowControlModel import BronkhorstFlowControlModel
    # from libs.SEWcontrolModel import SEWcontrolModel   # disabled since it is giving problems          
    #Wrapper for AtlasSensor
    from libs.atlasSensorWrapper import AtlasSensorWrapper      
    ##Model
    from libs.taskModel import TaskModel
    #Camera Adapter Class
    from libs.camAdapter import CamAdapter    
    ##Interface to offline image acquisition
    from libs.imageStorage import ImageStorage      
    ##Interface to NodeRed
    from libs.dataForwarder import DataForwarder
    ##Drop down menu
    from libs.dropDownMenu import DropDownMenu        
    ##EventManager
    from libs import eventManager
    ##ConfigurationManager
    from libs import configurationManager  
    ## pop-up windows of the main window
    from libs.enterProjectWindow import EnterProjectWindow

# logging
try:
    #Linux
    loggingDirectory = pathlib.Path.home()/'.local'/'share'/'DigiFlot'
    loggingDirectory.mkdir(exist_ok=True)
    headless, camera_connected, nodered_in_network, offline_image_storage, testrun = False, True, False, True, False
    windowCloseFlag = False
    # styleSheet = "QLabel{font-size: 35pt;} QFormLayout{font-size: 15pt;} QLineEdit{font-size: 15pt;} QListWidget{font-size: 15pt;} QGroupBox{font-size: 15pt;} QTableWidget{font-size: 15pt;} QTableWidgetItem{font-size: 15pt;} QHeaderView{font-size: 20pt;} QPushButton{font-size: 15pt;} QTabWidget{font-size: 15pt;} QMenuBar{font-size: 15pt;} QMenu{font-size: 15pt;}"
except:
    #Windows
    loggingDirectory = pathlib.Path.home()/'DigiFlot'
    loggingDirectory.mkdir(exist_ok=True)
    headless, camera_connected, nodered_in_network, offline_image_storage, testrun = False, False, False, False, False
    windowCloseFlag = True
    # styleSheet = "QLabel{font-size: 25pt;} QFormLayout{font-size: 25pt;} QLineEdit{font-size: 25pt;} QListWidget{font-size: 25pt;} QGroupBox{font-size: 20pt;} QTableWidget{font-size: 25pt;} QTableWidgetItem{font-size: 25pt;} QHeaderView{font-size: 25pt;} QPushButton{font-size: 30pt;} QTabWidget{font-size: 25pt;} QMenuBar{font-size: 25pt;} QMenu{font-size: 25pt;}"
loggingFilePath = loggingDirectory/"DigiFlot_log.txt"
logging.basicConfig(filename=str(loggingFilePath),
                    filemode='a',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%Y.%m.%d_%H:%M:%S',
                    level=logging.INFO)
logger = logging.getLogger('DigiFlot')

def _perceived_luminance(qc: QColor) -> float:
    return 0.2126 * qc.red() + 0.7152 * qc.green() + 0.0722 * qc.blue()

def _is_pure_black(qc: QColor) -> bool:
    return qc.red() == 0 and qc.green() == 0 and qc.blue() == 0

def _is_pure_white(qc: QColor) -> bool:
    return qc.red() == 255 and qc.green() == 255 and qc.blue() == 255

def _ensure_contrast_variant(qc: QColor, make_lighter: bool, min_lum_diff: float = 18.0):
    """Return a visibly lighter/darker variant. Handles pure black/white specially."""
    base_lum = _perceived_luminance(qc)

    # special-case black / white to guarantee change
    if _is_pure_black(qc):
        # return a visible dark gray when "darken" requested (fallback), otherwise a medium gray when lighten
        return QColor(30, 30, 30) if not make_lighter else QColor(60, 60, 60)
    if _is_pure_white(qc):
        return QColor(225, 225, 225) if make_lighter else QColor(200, 200, 200)

    # try iterative lighter/darker steps
    factors = [115, 125, 150, 160, 190, 230]
    candidate = qc
    for f in factors:
        candidate = qc.lighter(f) if make_lighter else qc.darker(f)
        if abs(_perceived_luminance(candidate) - base_lum) >= min_lum_diff:
            return candidate
    # fallback: return last candidate even if small change
    return candidate

def _adjust_font_color_if_equal(bg_qc: QColor, font_qc: QColor) -> QColor:
    """If font equals or too close to bg, return a contrasting font color (strong difference)."""
    # identical hex
    if bg_qc.name().lower() == font_qc.name().lower():
        bg_lum = _perceived_luminance(bg_qc)
        if bg_lum < 128:
            # dark bg => font must be very bright
            return _ensure_contrast_variant(bg_qc, make_lighter=True, min_lum_diff=150)
        else:
            return _ensure_contrast_variant(bg_qc, make_lighter=False, min_lum_diff=150)

    # if luminance too close, adjust similarly
    if abs(_perceived_luminance(bg_qc) - _perceived_luminance(font_qc)) < 10:
        bg_lum = _perceived_luminance(bg_qc)
        if bg_lum < 128:
            return _ensure_contrast_variant(bg_qc, make_lighter=True, min_lum_diff=110)
        else:
            return _ensure_contrast_variant(bg_qc, make_lighter=False, min_lum_diff=110)

    return font_qc

def compute_theme_colors(bg_hex: str, font_hex: str):
    """
    Return tuple (bg_hex, font_hex_adjusted, selected_hex, header_hex).
    header_hex will be same as selected_hex.
    """
    bg_q = QColor(bg_hex)
    font_q = QColor(font_hex)
    # ensure font contrast
    font_q = _adjust_font_color_if_equal(bg_q, font_q)

    lum = _perceived_luminance(bg_q)
    make_lighter = lum < 128
    selected_q = _ensure_contrast_variant(bg_q, make_lighter, min_lum_diff=18.0)
    # for headers we want maybe a slightly stronger contrast: compute with larger threshold
    header_q = _ensure_contrast_variant(bg_q, make_lighter, min_lum_diff=30.0)

    return bg_q.name(), font_q.name(), selected_q.name(), header_q.name()

def generate_dynamic_stylesheet(scale_factor: float,
                                bg_color: str = "#000000",
                                font_color: str = "#ffffff") -> str:
    """Build stylesheet using compute_theme_colors()."""
    bg_hex, font_hex, selected_hex, header_hex = compute_theme_colors(bg_color, font_color)

    base = {
        "QLabel": 20,
        "QFormLayout": 14,
        "QLineEdit": 14,
        "QListWidget": 14,
        "QGroupBox": 14,
        "QTableWidget": 14,
        "QTableWidgetItem": 14,
        "QHeaderView": 16,
        "QPushButton": 14,
        "QTabWidget": 14,
        "QMenuBar": 14,
        "QMenu": 14,
    }
    css_parts = [f"{widget}{{font-size: {int(size * scale_factor)}pt;}}" for widget, size in base.items()]
    css = " ".join(css_parts)

    css += f"""
        QWidget {{
            background-color: {bg_hex};
            color: {font_hex};
        }}

        /* Tabs */
        QTabBar::tab {{
            background: {bg_hex};
            color: {font_hex};
            padding: 1px 8px;
            border: 2px solid {font_hex};
            border-top-left-radius: 10px;
            border-top-right-radius: 10px;
        }}
        QTabBar::tab:selected {{
            background: {selected_hex};
            color: {font_hex};
            font-weight: bold;
        }}

        /* Table headers */
        QHeaderView::section {{
            background-color: {selected_hex};
            color: {font_hex};
            font-weight: bold;
            border: 1px solid {font_hex};
            padding: 4px;
        }}

        /* Buttons */
        QPushButton {{
            background-color: {selected_hex};
            color: {font_hex};
            border: 1px solid {font_hex};
            border-radius: 6px;
            padding: 6px 12px;
        }}
        QPushButton:hover {{
            background-color: {selected_hex};
            color: {font_hex};
            font-weight: bold;
        }}
        QPushButton:pressed {{
            background-color: {bg_hex};
            color: {font_hex};
            font-weight: bold;
        }}
    """
    return css


# Get default scale from screen DPI
_tmp_app = QGuiApplication(sys.argv)
dpi = _tmp_app.primaryScreen().logicalDotsPerInch()
default_scale_factor = dpi / 96  # baseline at 96 DPI
_tmp_app.quit()

class MainWindow(QMainWindow):
    def __init__(self, camera_connected, nodered_in_network, offline_image_storage, testrun):
        super().__init__()

        # Hide Window Close Button
        self.setWindowFlag(Qt.WindowCloseButtonHint, windowCloseFlag)
        try:
            ver = version("digiflot")
        except PackageNotFoundError:
            ver = "dev"   # fallback if running from source
        self.setWindowTitle(f"DigiFlot v{ver}")
        
        #self.setWindowTitle('DigiFlot')
        self.dfont = ("Helvetica",50) # this must be deleted
        self.openWindows = []
        self.nodered_in_network = nodered_in_network
        self.offline_image_storage = offline_image_storage

        atlasSensor = AtlasSensor()
        lidar = Lidar()
        lidar.connectToLidar(atlasSensor)

        #instantiate model
        taskModel = TaskModel(None, atlasSensor, lidar)

        # prepare dictionary of wrappers for atlasSensor and lidar to give a standard inferface for all sensors by implementing the abstract FormalHardwareInferface
        deviceDictionary = {MOD : AtlasSensorWrapper(taskModel, atlasSensor, MOD) for MOD in atlasSensor.modules_list if MOD != "LIDAR"}
        if "LIDAR" in atlasSensor.modules_list:
            deviceDictionary["LIDAR"] = lidar
        #Set tolerances for pH-Sensor
        if "pH" in deviceDictionary.keys():
            deviceDictionary["pH"].setRelativeTolerance(lower_tolerance=0.97, upper_tolerance=1.03)

        # initialize process-shared configuration
        configurationManager.initializeSharedConfiguration(path=loggingDirectory)
        # load configuration from default working folder if there is one, plus avoid overriding default config by changing the path
        configurationManager.tryToUpdateSharedConfiguration(path=taskModel.workingfolder)
        # obtain configuration for MainWindow
        configuration = configurationManager.getConfig("MainWindow")

        # --- Font scaling and color setup ---
        # Load stored font scale, or fall back to default DPI-based value
        self.scale_factor = float(configuration["font scale"])
        self.bg_color = configuration["background color"]
        self.font_color  = configuration["font color"]
        self.update_fontscale_colors(self.scale_factor,self.bg_color,self.font_color)

        # start prompt for entering the project id
        projectWindow = EnterProjectWindow()
        self.openWindows.append(projectWindow)
        projectWindow.show()

        self.camAdapter = CamAdapter(taskModel, className=configuration["camera model class"])
        if camera_connected:
            self.camAdapter.startStream() # start the image fetch loop on a separate loop

        camInstance = self.camAdapter.getCamInstance()
        taskModel.setCamera(camInstance)

        #offline image storage process
        self.imageStorage = ImageStorage(camInstance)
        if offline_image_storage:
            self.imageStorage.startOfflineStorageService()

        #connection to Bronkhorst Flow Control
        self.bronkhorstFlowControlModel = BronkhorstFlowControlModel()

        #connection to SEW
        # self.sewControl = SEWcontrolModel() # disabled since it is giving problems  

        #instantiate tab views
        tabViewSetup = TabViewSetup(taskModel, camInstance, atlasSensor, lidar)
        tabViewRun = TabViewRun(taskModel)
        tabViewInformation = TabViewInformation(taskModel, lidar)
        tabViewRestartExit = TabViewRestartExit(self.camAdapter)
        tabViewCalibCam = self.camAdapter.getCalibCamInstance()
        tabViewCalibLidar = TabViewCalibLidar(self, lidar, atlasSensor)
        tabViewCalibSensors = TabViewCalibSensors(atlasSensor, deviceDictionary)
        tabViewBronkhorstFlowControl = TabViewBronkhorstFlowControl(self.bronkhorstFlowControlModel)
        # tabViewSEWControl = TabViewSEWControl(self.sewControl) # disabled since it is giving problems  

        #TabWidget that manages all the tabs
        self.tabs = QTabWidget(self)
        #Add Tabs to QTabWidget
        self.tabs.addTab(tabViewSetup, "Setup")
        self.tabs.addTab(tabViewRun, "Run")
        self.tabs.addTab(tabViewInformation, "Information")
        self.tabs.addTab(tabViewRestartExit, "Restart/Exit")
        if atlasSensor.connectedSuccessfully():
            self.tabs.addTab(tabViewCalibSensors, "Calibrate Sensors")
        if camInstance.connectedSuccessfully():
            self.tabs.addTab(tabViewCalibCam, "Calibrate camera")
        if lidar.connectedSuccessfully():           
            self.tabs.addTab(tabViewCalibLidar, "Calibrate LIDAR")
        if self.bronkhorstFlowControlModel.connectedSuccessfully():
            self.tabs.addTab(tabViewBronkhorstFlowControl, "Flow Control")
        # if self.sewControl.connectedSuccessfully(): # disabled since it is giving problems  
        #     self.tabs.addTab(tabViewSEWControl, "SEW Control")

        # Hide run tab until setup is complete
        self.tabs.setTabVisible(1, False)

        # add QTabWidget to main layout
        self.setCentralWidget(self.tabs)

        #Register event of a change of tab
        eventManager.registerEvent("tabChanged", self.tabs.currentChanged)
        eventManager.connectToEvent("exitButtonClicked", self.close)

        self.dataForwarder = DataForwarder(taskModel, camInstance, controller=None)

        #instantiate controller and add it as attribute to mainWindow, otherwise the controller gets destructed after init of mainWindow
        self.controller = Controller(self.tabs, self.camAdapter, atlasSensor, lidar, self.bronkhorstFlowControlModel, taskModel, deviceDictionary, tabViewSetup, tabViewRun, tabViewInformation, tabViewRestartExit, tabViewCalibCam, tabViewCalibLidar, tabViewCalibSensors, tabViewBronkhorstFlowControl, self.imageStorage, self.dataForwarder) #self.sewControl, removed due to issues

        self.dataForwarder.setController(self.controller)
        if nodered_in_network:
            self.dataForwarder.startDataForwarderService()

        # add QMenu to main layout
        self.dropDownMenu = DropDownMenu(self)

        if testrun:
            self.closeEvent(None)
            exit()

    def closeEvent(self, event):
        self.bronkhorstFlowControlModel.setAirFlow(0.0)
        # self.sewControl.setRotorSpeed(0.0) #disabled for now
        self.controller.fetch_measurement_timer.stop()
        self.controller.calib_cam_timer.stop()
        self.dataForwarder.finishProcessesAndQueues()
        self.imageStorage.finishProcessesAndQueues()
        self.camAdapter.finishProcessesAndQueues()
        try:
            configurationManager.storeToJson()
        except:
            logger.error(f"Could not write to {str(configurationManager.json_path/'configuration.json')}, probably because the file was in use.")
        # Close all open windows
        for window in self.openWindows:
            window.close()            
        if event is not None:
            # Proceed with the default close event
            super().closeEvent(event)

    def update_fontscale_colors(self, scale: float, bg_color: str, font_color: str):
        """Apply a new font scaling factor to the entire app."""
        self.scale_factor = scale
        self.bg_color = bg_color
        self.font_color = font_color
        
        self.setStyleSheet(generate_dynamic_stylesheet(scale, self.bg_color, self.font_color))
        
        # Persist new value in shared config
        config = configurationManager.getConfig("MainWindow")
        config["font scale"] = scale     
        config["background color"] = self.bg_color
        config["font color"] = self.font_color   
        configurationManager.storeToJson()


def main(headless = False, camera_connected = True, nodered_in_network = True, offline_image_storage = True, testrun = False):
    if headless:
        app = QApplication(sys.argv+['-platform', 'minimal'])
    else:
        app = QApplication(sys.argv)
    app.setStyleSheet(generate_dynamic_stylesheet(default_scale_factor))

    
    #custom_font = QFont()
    #custom_font.setWeight(40)
    #app.setFont(custom_font, "QLabel")
    mainWindow = MainWindow(camera_connected, nodered_in_network, offline_image_storage, testrun)
    #mainWindow.resize(800, 600)
    mainWindow.showMaximized()
    return app.exec()

if __name__=="__main__":
    main(headless, camera_connected, nodered_in_network, offline_image_storage, testrun)

