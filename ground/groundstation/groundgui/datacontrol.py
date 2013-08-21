# This file provides the DataControlWindow class, which allows the user
#  to control the time interval observed by its associated FitsReader.
#
# Intended public interface:
# DataControlWindow( <FitsManager instance> ): a PyGUI Window object that
#  has various controls for the manager passed to it.
#  It can set the start and end times for the manager, and can have "live"
#  mode enabled, which will automatically update the manager every second or so.

from GUI import Label, TextField, CheckBox, Window, Button, Task, Row
from GUI.Alerts import alert

import datetime
from os.path import sep as PATH_SEPARATOR

from ggutils import PADDING

import numpy
from exceptions import AttributeError

import pickle

from devices import TELESCOPE_10GHZ, TELESCOPE_15GHZ

AUTO_UPDATE_INTERVAL = 5




def parse_timedelta( s ):
    hour,minute,second = (int(field) for field in s.split(':'))
    return datetime.timedelta(hours=hour,minutes=minute,seconds=second)
def parse_datetime( s ):
    day, time = s.split(' ')
    year,month,day = (int(field) for field in day.split('/'))
    hour,minute,second = (int(field) for field in time.split(':'))
    return datetime.datetime(year,month,day,hour,minute,second)

class DataControlWindow( Window ):
    """Controls the data everyone sees."""

    resizable = True
    
    item_width = 200
    duration = datetime.timedelta(minutes=15)
    time = datetime.datetime(2011,8,8,18,0,0)
    
    def __init__( self, manager ):
        super(DataControlWindow, self).__init__(title="Data Control")
        
        self.manager = manager

        duration_text = ':'.join(( '%02d'%(self.duration.seconds // 3600),
                                   '%02d'%((self.duration.seconds%3600)//60),
                                   '%02d'%(self.duration.seconds % 60) ))
        self.folder_label = Label( text=manager.folder )
        self.time_field = TextField( text=self.time.strftime('%Y/%m/%d %H:%M:%S'),
                                     width=self.item_width,
                                     enter_action=self.update )
        self.duration_field = TextField( text=duration_text,
                                         width=self.item_width,
                                         enter_action=self.update )
        self.live_checkbox = CheckBox( 'Live', action=self.toggle_live )
        self.revsync_checkbox = CheckBox( 'Rev-sync', action=self.toggle_revsync )
        self.averaging_checkbox = CheckBox( 'Average data', action=self.toggle_averaging )
        self.convert_checkbox = CheckBox('Convert files', action=self.toggle_convert)
        self.update_button = Button( title='Refresh', action=self.update )
        self.auto_updater = Task( self.update, AUTO_UPDATE_INTERVAL,
                                  start=False, repeat=True )

        time_row = Row([Label('Start: '), self.time_field])
        duration_row = Row([Label('Duration: '), self.duration_field])
        
        self.place_column( [self.folder_label, time_row, duration_row,
                            self.live_checkbox, self.revsync_checkbox,
                            self.averaging_checkbox, self.convert_checkbox,
                            self.update_button],
                           left=PADDING, top=PADDING )
        self.shrink_wrap()
    
    def toggle_live( self ):
        self.update()
        if self.live_checkbox.value:
            self.time_field.enabled = False
            self.auto_updater.start()
        else:
            self.time_field.enabled = True
            self.auto_updater.stop()
    
    def toggle_revsync( self ):
        TELESCOPE_10GHZ.sync = self.revsync_checkbox.value
        TELESCOPE_15GHZ.sync = self.revsync_checkbox.value
    
    def toggle_averaging( self ):
        self.manager.averaging = self.averaging_checkbox.value
        self.manager.clear_cache()
    
    def toggle_convert( self ):
        self.manager.set_convert(self.convert_checkbox.value)
        
    def update( self ):
        try:
            duration = parse_timedelta(self.duration_field.text)
            if duration.seconds < 0:
                raise ValueError()
            self.duration = duration
        except ValueError:
            alert('stop', "Invalid duration. Requires 'hour:minute:second'.")
            return
            
        if self.live_checkbox.value:
            try:
                end = self.manager.get_last_filetime()
            except IndexError:
                print "No _ext.fits files exist in the given directory tree."
                return
            start = end - self.duration
        else:
            try:
                self.time = parse_datetime(self.time_field.text)
            except ValueError:
                alert('stop', "Invalid time. Requires 'year/month/day hour:minute:second'.")
                return
            start = self.time
            end = start + self.duration
        
        self.manager.set_interval( start, end )
        self.manager.read_data()
        self.update_plotwindow()

    def set_plotwindow(self, plotwindow):
        """Save reference to the plot window to trigger updates"""
        self._plotwindow = plotwindow

    def update_plotwindow(self):
        """Trigger update of the attached plot window"""
        self._plotwindow.plot_update()
