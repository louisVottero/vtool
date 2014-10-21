# Copyright (C) 2014 Louis Vottero louis.vot@gmail.com    All rights reserved.

import sys, random
import qt_ui

if qt_ui.is_pyqt():
    from PyQt4 import QtGui, QtCore, Qt, uic
if qt_ui.is_pyside():
    from PySide import QtCore, QtGui
    
class TestWidget(QtGui.QWidget):
    

    
    def __init__(self):
        super(TestWidget, self).__init__()
        
        self.text = 'gooooooooobers'
    def paintEvent(self, e):

        painter = QtGui.QPainter()
        
        painter.begin(self)
        self.draw_lines(painter)
        self.draw_frame(painter)
        painter.end()
        
        
    def draw_frame(self, painter):
        
        pen = QtGui.QPen(QtCore.Qt.black)
        painter.setPen(pen)
        
        size = self.size()
        
        width = size.width()
        height = size.height()
                
        #painter.drawLine( 10, height-21, width-11, height-21 )
        
        
        section = (width-21.00)/24.00
        accum = 10.00
        
        for inc in range(0, 25):
            
            value = inc
            
            if inc > 12:
                value = inc-12
            painter.drawLine(accum, height-21, accum, height-31)
            
            painter.drawText(accum-15, height-16, 30,10, QtCore.Qt.AlignCenter, str(value))
            
            accum+=section
            
        
        
        
    def draw_lines(self, painter):
      
        pen = QtGui.QPen(QtCore.Qt.red)
        pen.setWidth(2)
        
      
        painter.setPen(pen)
        
        size = self.size()
        
        for i in range(2000):
            x = random.randint(10, size.width()-11)
            #y = random.randint(1, size.height()-1)
               
            painter.drawLine(x,10,x,size.height()-41)     
    
    
def main():
    
    APP = QtGui.QApplication(sys.argv)
    test = TestWidget()
    test.show()
    
    sys.exit(APP.exec_())
    

if __name__ == '__main__':
    main()
    