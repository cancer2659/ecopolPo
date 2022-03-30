from PyQt5 import QtWidgets, QtGui, QtCore, uic
import PyQt5
import xlwings
import time
from elements.sql.addNewPosition import addNewPositionToArhive, addProposalNameToArhive
from elements.sql.equip_arhive import add_equip_params_in_sql
from elements.sql.getsQuery import get_all_params_erpe
from widgets.objInf_w.objInfoWindow import mainObj
from elements.sql.connectSql import connectToSql
from elements.sql.pushToCmbFromSql import getUniqFromColumn, getChanelDepth
from elements.widgetsOperation.addPositionToCmb import addPositionToCMB
from widgets.erpe_page.changeERPEparams import ObjParamERPEWindow
from widgets.reCalcuateItem.reCalcItem import RecalculationItem
from widgets.menuParams.globalParams import GlobalParamsWindow
from elements.fileOperation.manualUpdateCalculation import manual_update_calculation

class ErpeWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        QtWidgets.QMainWindow.__init__(self, parent)
        self.connect = connectToSql()
        self.parent = parent
        uic.loadUi("widgets/erpe_page/erpe_window.ui", self)

        self.pix = QtGui.QPixmap('img/ЭРПЭ.jpg')
        self.lb_img.setPixmap(self.pix)

        self.btn_back.clicked.connect(self.back_page)
        self.btn_calculate.clicked.connect(self.calculate)
        #
        # self.allParamsPTO = get_all_params()

        positions = getUniqFromColumn(self.connect[0],
                                      self.connect[1],
                                      tableName='arhive',
                                      columnName='position',
                                      findParam=mainObj.city,
                                      findParamCategory='city',
                                      findParam2=mainObj.location,
                                      findParamCategory2='location')
        addPositionToCMB(positions, self.cmb_position)
        self.cmb_position.setCurrentText('')

        self.mn_globalParams.triggered.connect(self.change_global_params)
        self.menu_bth_renew.triggered.connect(self.renew_position)
        self.mn_price_params.triggered.connect(self.change_price_params)
        # self.update_data_in_sql.triggered.connect(lambda e: manual_update_calculation(self))

        self.initial_cmb_filling()

        self.cmb_cw.currentTextChanged.connect(self.change_cw)
        self.cmb_cp.currentTextChanged.connect(self.cp_change)

    def initial_cmb_filling(self):
        para_names_in_sql = ['Материал',
                             'Перфорация, мм',
                             'Ширина канала, мм',
                             'Привод',
                             'Протокол',
                             'ШУ',
                             'Высота выгрузки, мм',
                             'Ссылка на ячейки',
                             'Ссылка на файл']

        self.allParams = get_all_params_erpe(para_names_in_sql)
        try:
            self.cmb_gap.clear()
            self.cmb_mat.clear()
            self.cmb_cw.clear()
            self.cmb_ip.clear()
            self.cmb_cp.clear()
            self.cmb_hl.clear()
        except:
            pass

        addPositionToCMB(self.allParams['Перфорация, мм'], self.cmb_gap)
        addPositionToCMB(self.allParams['Материал'], self.cmb_mat)

        channelWidth = []
        for x in range(self.allParams['Ширина канала, мм'].__len__()):
            channelWidth.append(self.allParams['Ширина канала, мм'][x][0])

        addPositionToCMB(channelWidth, self.cmb_cw)
        addPositionToCMB(self.allParams['Привод'], self.cmb_ip)
        addPositionToCMB(self.allParams['ШУ'], self.cmb_cp)
        addPositionToCMB(self.allParams['Высота выгрузки, мм'], self.cmb_hl)

        self.cp_change()
        self.change_cw()

    def cp_change(self):
        if self.cmb_cp.currentText() == "Нет":
            self.cmb_protokol.clear()
            self.cmb_protokol.addItem("Нет")
            self.cmb_protokol.setEnabled(False)

        else:
            self.cmb_protokol.clear()
            addPositionToCMB(self.allParams['Протокол'], self.cmb_protokol)
            self.cmb_protokol.setEnabled(True)

    def back_page(self):
        self.hide()
        self.parent.show()

    def change_cw(self):
        try:
            self.cmb_ch.clear()

            # get channel parameters from arhive `self.allParamsPTO`
            channelw_d = []
            for x in range(self.allParams['Ширина канала, мм'].__len__()):
                if int(self.allParams['Ширина канала, мм'][x][0]) == int(self.cmb_cw.currentText()):
                    channelw_d.append(self.allParams['Ширина канала, мм'][x][1])
                    channelw_d.append(self.allParams['Ширина канала, мм'][x][2])
                else:
                    pass
            # create new array of channels dept for `cmb_cw.currentText()`
            channel_depth = []
            for ix in range(int(channelw_d[0]), int(channelw_d[1]), 100):
                channel_depth.append(ix)

            # add array with channel depth int to `self.cmb_c`
            addPositionToCMB(channel_depth, self.cmb_ch)

        except:
            pass

    def renew_position(self):
        r = RecalculationItem(self)
        r.show()

    def change_price_params(self):
        w = GlobalParamsWindow(self)
        w.show()

    def change_global_params(self):
        w = ObjParamERPEWindow(self)
        w.show()
        w.updateSignal.connect(self.initial_cmb_filling)

    def calculate(self):
        mainObj.erpe.gap = self.cmb_gap.currentText()
        mainObj.erpe.channelWidth = self.cmb_cw.currentText()
        mainObj.erpe.channelDepth = self.cmb_ch.currentText()
        mainObj.erpe.unloadH = self.cmb_hl.currentText()
        mainObj.erpe.driveIP = self.cmb_ip.currentText()
        mainObj.erpe.material = self.cmb_mat.currentText()
        mainObj.erpe.controlPanel = self.cmb_cp.currentText()
        mainObj.erpe.connection = self.cmb_protokol.currentText()
        mainObj.position = self.cmb_position.currentText()

        self.calculate_erpe(self.allParams, mainObj)

    def calculate_erpe(self, paramsArr, mainObj):
        import xlwings
        import time

        def add_value_in_excel_cell(linksArr, findParam, value):
            for x in (range(linksArr.__len__())):
                if linksArr[x][0] == findParam:
                    wb.sheets[str(f'{linksArr[x][1]}')].range(f'{linksArr[x][2]}').value = value


        wb = xlwings.Book(str(paramsArr['Ссылка на файл'][0][1]).replace('/', '\\'))

        from elements.fileOperation.pushGepParamToCalculation import pushParamsToFile
        pushParamsToFile(xlWorkBook=wb)

        add_value_in_excel_cell(paramsArr['Ссылка на ячейки'], 'Материал', mainObj.erpe.material)
        add_value_in_excel_cell(paramsArr['Ссылка на ячейки'], 'Ширина канала', mainObj.erpe.channelWidth)
        add_value_in_excel_cell(paramsArr['Ссылка на ячейки'], 'Прозор', mainObj.erpe.gap)
        add_value_in_excel_cell(paramsArr['Ссылка на ячейки'], 'Глубина канала', mainObj.erpe.channelDepth)
        add_value_in_excel_cell(paramsArr['Ссылка на ячейки'], 'Высота выгрузки', mainObj.erpe.unloadH)
        add_value_in_excel_cell(paramsArr['Ссылка на ячейки'], 'Привод', mainObj.erpe.driveIP)
        add_value_in_excel_cell(paramsArr['Ссылка на ячейки'], 'ШУ', mainObj.erpe.controlPanel)
        add_value_in_excel_cell(paramsArr['Ссылка на ячейки'], 'Протокол', mainObj.erpe.connection)

        add_value_in_excel_cell(paramsArr['Ссылка на ячейки'], 'Дата', time.strftime("%d.%m.%Y"))
        add_value_in_excel_cell(paramsArr['Ссылка на ячейки'], 'Менеджер', mainObj.manager)
        add_value_in_excel_cell(paramsArr['Ссылка на ячейки'], 'Страна', mainObj.country)
        add_value_in_excel_cell(paramsArr['Ссылка на ячейки'], 'Город', mainObj.city)
        add_value_in_excel_cell(paramsArr['Ссылка на ячейки'], 'Объект', mainObj.object)
        add_value_in_excel_cell(paramsArr['Ссылка на ячейки'], 'Место установки', mainObj.location)
        add_value_in_excel_cell(paramsArr['Ссылка на ячейки'], 'Позиция по проекту', mainObj.position)
        add_value_in_excel_cell(paramsArr['Ссылка на ячейки'], 'Страна', mainObj.country)
        add_value_in_excel_cell(paramsArr['Ссылка на ячейки'], 'Блан организации', mainObj.company)

        # get information from calculation
        mainObj.erpe.weight = wb.sheets['Спецификация'].range('C2').value
        mainObj.erpe.mark = wb.sheets['Спецификация'].range('A2').value
        mainObj.erpe.power = wb.sheets['Спецификация'].range('D2').value
        mainObj.erpe.price = wb.sheets['Спецификация'].range('C101').value
        mainObj.erpe.controlPanel_price = wb.sheets['Спецификация'].range('D101').value

        mainObj.erpe.description_to_rdc = wb.sheets['Цена'].range('I5').value

        mainObj.erpe.proposal_ID = addNewPositionToArhive(city=mainObj.city,
                                                         object=mainObj.object,
                                                         location=mainObj.location,
                                                         position=mainObj.position,
                                                         mark=mainObj.erpe.mark,
                                                         manager=mainObj.manager,
                                                         equip_price=mainObj.erpe.price,
                                                         cp_price=mainObj.erpe.controlPanel_price,
                                                         weight=mainObj.erpe.weight,
                                                         ip=str(f'IP {mainObj.erpe.driveIP}'),
                                                         power=mainObj.erpe.power,
                                                         material=mainObj.erpe.material,
                                                         executor=mainObj.user,
                                                         equip_code=mainObj.erpe.equipDescription_code,
                                                         description=mainObj.erpe.description_to_rdc,
                                                         country=mainObj.country,
                                                         tkp_company=mainObj.company)

        mainObj.erpe.name_proposal = str('ТКП №' + str(mainObj.erpe.proposal_ID) + ' '\
                                        + str(mainObj.city) + ' '\
                                        + str(mainObj.object) + ' '\
                                        + str(time.strftime("%d.%m.%Y")))

        add_value_in_excel_cell(paramsArr['Ссылка на ячейки'], 'Номер предложения', mainObj.erpe.proposal_ID)
        #
        mainObj.erpe.name_calculation = wb.sheets['Цена'].range('I3').value
        #
        addProposalNameToArhive(int(mainObj.erpe.proposal_ID), "ТКП №" + str(mainObj.erpe.name_calculation) + ".doc")
        #
        add_equip_params_in_sql('erpe', mainObj)

        from elements.fileOperation.proposal_forming import create_proposal
        create_proposal(calculationFile=wb,
                        proposalSample=str(paramsArr['Ссылка на файл'][1][1]).replace('/', '\\'),
                        proposalSavingDirectory="D:\\1_newProgram(ver.2)\\docs\\proposals",
                        fileName=mainObj.erpe.name_proposal)

        wb.save(f'D:\\1_newProgram(ver.2)\\docs\\initial\\{str(mainObj.erpe.name_calculation)}.xlsx')
        #
        wb.app.quit()


