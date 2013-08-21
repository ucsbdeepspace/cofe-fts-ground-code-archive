from GUI import Frame, Row, Column, Label, Button, TextField,\
     CheckBox, RadioButton, RadioGroup, Window, Application
from GUI.Alerts import alert
from GUI.Files import FileRef, DirRef
from GUI.FileDialogs import request_old_files

import psplot

global option_window

class LabeledItemFrame( Frame ):
    def __init__( self, title, item, width=None ):
        Frame.__init__( self )
        self.title_label = Label(text=title)
        self.item = item
        self.place_row([self.title_label, self.item],left=0,top=0)
        self.shrink_wrap()
        if width is not None:
            self.width = width

class SelectionFrame( Frame ):
    width = 400
    def __init__( self, directory, callback ):
        Frame.__init__( self )
        self.directory = directory
        self.callback = callback
        self.refs = []
        self.channels = []

        label = Label(text='-----', width=SelectionFrame.width)
        self.label_frame = LabeledItemFrame( "Files:", label )
        self.select_button = Button(title='Select', action=self.select,
                                        width=100)
        field = TextField(text='', width=SelectionFrame.width)
        self.channel_frame = LabeledItemFrame( "Channels:", field )

        self.place_column([self.label_frame, self.select_button,
                           self.channel_frame], left=0, top=0)
        self.shrink_wrap()

    def select( self ):
        self.refs = request_old_files(default_dir=self.directory)
        if self.refs:
            self.directory = self.refs[0].dir
            if len(self.refs) > 4:
                t = ', '.join([ref.name for ref in self.refs[:3]]+\
                              ['...'] + [self.refs[-1].name])
            else:
                t = ', '.join([ref.name for ref in self.refs])
            self.label_frame.item.text = t
            self.callback()
    
    def get_channels( self ):
        return [s.strip() for s in self.channel_frame.item.text.split(',')]

class SelectionWindow( Window ):
    def __init__( self ):
        Window.__init__( self, title='File/channel selection',
                         resizable=False )
        self.selection_frames = []
        self.last_selected_directory = DirRef('.')
        self.enter_button = Button(title='Plot',action=self.plot,width=200)
        self.add_frame()

    def add_frame( self ):
        if all((frame.refs for frame in self.selection_frames)):
            top = (self.selection_frames[-1].bottom+10 if self.selection_frames else 5)
            new_frame = SelectionFrame(self.last_selected_directory,
                                       self.add_frame)
            self.selection_frames.append(new_frame)
            self.place(new_frame, left=0, top=top)
            self.place(self.enter_button, left=0, top=new_frame)
            self.shrink_wrap()

    def plot( self ):
        global option_window
        options = option_window.parse()
        if options is None:
            return
        pairs = [(frame.refs, frame.get_channels())
                 for frame in self.selection_frames
                 if frame.refs and frame.get_channels()]
        try:
            psplot.plot(pairs, options)
        except ValueError as e:
            alert('stop', e.message)

class OptionWindow( Window ):
    width = 400
    def __init__( self ):
        Window.__init__( self, title='Options' )
        self.resolution_field = TextField(text='1',
                                          width=OptionWindow.width)
        resolution_frame = LabeledItemFrame( 'Resolution (Hz):',
                                             self.resolution_field )

        self.frequency_field = TextField(text='6400',
                                         width=OptionWindow.width)
        frequency_frame = LabeledItemFrame( 'Sampling frequency (Hz)',
                                            self.frequency_field )

        detrending_buttons = [RadioButton(title='none',
                                          value='none'),
                              RadioButton(title='mean',
                                          value='mean'),
                              RadioButton(title='linear',
                                          value='linear')]
        detrending_column = Column(detrending_buttons)
        detrending_frame = LabeledItemFrame('Detrending',
                                            detrending_column)
        self.detrending_group = RadioGroup(detrending_buttons)
        self.detrending_group.value = 'none'

        windowing_buttons = [RadioButton(title='Hanning',
                                          value='hanning'),
                              RadioButton(title='none',
                                          value='none'),
                              RadioButton(title='Blackman',
                                          value='blackman'),
                              RadioButton(title='Hamming',
                                          value='hamming'),
                              RadioButton(title='Bartlett',
                                          value='bartlett')]
        windowing_column = Column(windowing_buttons)
        windowing_frame = LabeledItemFrame('Windowing',
                                           windowing_column)
        self.windowing_group = RadioGroup(windowing_buttons)
        self.windowing_group.value = 'hanning'

        self.xscale_box = CheckBox(title='X-axis log scale', value=0)
        self.yscale_box = CheckBox(title='Y-axis log scale', value=1)

        self.sqrt_box = CheckBox(title='Square root', value=0)

        self.against_time_box = CheckBox(title='Plot against time',
                                         value=0,
                                         action=self.toggle_against_time)
        self.slice_field = TextField(text='0:10000:1', width=OptionWindow.width,
                                     enabled=self.against_time_box.value)
        slice_frame = LabeledItemFrame('Range (start:stop:step)',
                                       self.slice_field)

        self.place_column( [resolution_frame, frequency_frame,
                            detrending_frame, #windowing_frame,
                            # Commented because we may never want to use it
                            self.xscale_box, self.yscale_box,
                            self.sqrt_box, self.against_time_box,
                            slice_frame],
                           left=5, top=5 )
        self.shrink_wrap()

    def toggle_against_time( self ):
        self.slice_field.enabled = self.against_time_box.value
        if self.against_time_box.value:
            self.xscale_box.value = 0
            self.yscale_box.value = 0
        for item in [self.resolution_field, self.frequency_field,
                     self.detrending_group, self.windowing_group,
                     self.sqrt_box, self.xscale_box, self.yscale_box]:
            item.enabled = not self.against_time_box.value

    def parse( self ):
        try:
            resolution = float(self.resolution_field.text)
        except ValueError:
            alert('stop', "Resolution field requires a float.")
            return
        try:
            frequency = float(self.frequency_field.text)
        except ValueError:
            alert('stop', "Frequency field requires a float.")
            return
        try:
            start,stop,step = [int(x) for x in self.slice_field.text.split(':')]
        except ValueError:
            alert('stop', "Range field requires start:stop:step, e.g. 50:1000:10 to plot every tenth sample from the fiftieth to thousandth")
            return
            
        detrending = self.detrending_group.value
        windowing = self.windowing_group.value
        xscale = ('log' if self.xscale_box.value else 'linear')
        yscale = ('log' if self.yscale_box.value else 'linear')
        sqrt = self.sqrt_box.value
        against_time = self.against_time_box.value
        return { 'resolution':resolution, 'frequency':frequency,
                 'detrending':detrending, 'xscale':xscale,
                 'yscale':yscale, 'sqrt':sqrt,
                 'against_time':against_time,
                 'windowing':windowing, 'slice':slice(start,stop,step)}
        

class PSApplication( Application ):
    def open_app( self ):
        global option_window
        SelectionWindow().show()
        option_window = OptionWindow()
        option_window.show()
