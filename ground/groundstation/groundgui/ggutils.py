# This file defines several constants and functions that are used in
#  the other groundgui files.


from GUI import Font, Frame, Grid, Row, Label
from devices import GYRO_HID, GYRO_MCD, MAGNETOMETER, ASHTECH,\
    ANALOGCHANNELS, TELESCOPE_10GHZ, TELESCOPE_15GHZ
from math import ceil


# This controls the layout of the plotting checkboxes and channel data labels.
#  Each device gets a grid of items associated with it, and the grids are split
#  into rows, The contents of each tuple in LAYOUT determines which device grids
#  are on that row, and the number paired with each device determines how many
#  rows are in that device's grid.
DEFAULT_LAYOUT = ( ( (GYRO_HID, 6), (GYRO_MCD,2), (ASHTECH, 6) ),
                   ( (MAGNETOMETER, 6), (ANALOGCHANNELS, 8), ),
                   ( (TELESCOPE_10GHZ, 9), (TELESCOPE_15GHZ, 9) ) )

# Default padding.
PADDING = 5

# Fonts for grid entries.
TITLE_FONT = Font('Helvetica', 16, [])
ENTRY_FONT = Font('Helvetica', 12, [])



def frame_items( items, layout=DEFAULT_LAYOUT ):
    """Places a set of titled grids in a Frame according to the contents of LAYOUT."""
    result = Frame()
    top = 0
    for row_info in layout:
        grids = []
        for device,height in row_info:
            channel_items = [items[device][channel] for channel in device.iterchannels(clock=False)]
            grids.append( make_grid(device.display_name, channel_items, height) )
        row = Row( grids, spacing=3*PADDING )
        result.place( row, left=0, top=top )
        top = row.bottom + 3*PADDING
    result.shrink_wrap()
    return result

def make_grid( title, items, num_rows ):
    """Returns a grid with the given title, items, and number of rows."""
    # Items are laid out top-to-bottom, left-to-right.
    num_columns = int(ceil( len(items) / float(num_rows) ))
    
    rows = [ [items[i] for i in range(row_index, len(items), num_rows)]
             for row_index in range(num_rows) ]
    
    top_row = [Label(title, font=TITLE_FONT)]
    for _ in range(num_columns-1):
        top_row.append(Label('(cont.)', font=ENTRY_FONT))
    return Grid( [top_row]+rows )