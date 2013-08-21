from GUI import Label, CheckBox, TextField, Row, Window

import devices
from devices import DEVICES, TELESCOPE_10GHZ, TELESCOPE_15GHZ

import ggutils
from ggutils import PADDING


RMS_DEVICES = [TELESCOPE_10GHZ, TELESCOPE_15GHZ]

def rms(data):
    m = data.mean()
    return (sum(((x-m)**2 for x in data))/len(data))**.5



class ChannelLabel( Label ):
    def __init__( self, channel ):
        self._prefix = channel + ': '
        self._value = '<unavailable>'
        super(ChannelLabel, self).__init__( self._prefix + self._value,
                                            font=ggutils.ENTRY_FONT )
    
    def set_value( self, value ):
        self._value = str(value)
        self.text = self._prefix + self._value
        
class DataViewWindow( Window ):
    """Displays the value of every channel."""
    resizable = True

    n_rms_samples = 100
    
    def __init__( self, manager ):
        super(DataViewWindow, self).__init__(title="Data View")
        self.manager = manager
        self.manager.listeners.append( self )

        self.rms_checkbox = CheckBox('RMS', action=self.update_labels)
        self.rms_samples_field = TextField(text=str(self.n_rms_samples),
                                           width=100, enter_action=self.set_n_rms_samples)
            
        self.labels = devices.channel_parallels(
                        lambda d,c: ChannelLabel(c.display_name) )
        self.build()
    
    def build( self ):
        """Lays out the components of the window."""
        # We'll have one grid of labels for each device,
        #  laid out in four rows.

        top_row = Row( [self.rms_checkbox, self.rms_samples_field] )
        label_frame = ggutils.frame_items( self.labels )
        self.place( top_row, left=PADDING, top=PADDING )
        self.place( label_frame, left=PADDING, top=top_row.bottom+PADDING )
        self.shrink_wrap()

    def set_n_rms_samples( self ):
        try:
            n_rms_samples = int(self.rms_samples_field.text)
            if n_rms_samples <= 0:
                raise ValueError()
            self.n_rms_samples = n_rms_samples
            if self.rms_checkbox.value:
                self.update_labels()
        except ValueError:
            print "Invalid number of RMS samples. Enter a positive integer."

    def update_labels( self ):
        print "Updating labels."
        for device,checkboxes in self.labels.iteritems():
            for channel,checkbox in checkboxes.iteritems():
                if channel.data is None:
                    value = '<unavailable>'
                elif self.rms_checkbox.value:
                    value = rms(channel.data[-self.n_rms_samples:])
                else:
                    value = channel.data[-1]
                self.labels[device][channel].set_value(value)
    
    def note_manager_updated( self ):
        """Updates the data display text."""
        self.update_labels()
