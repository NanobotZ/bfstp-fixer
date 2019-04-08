import os
import sys
import struct
import time

def fix(full_path): # returns true if fixer didn't have any problems
	_, file_name = os.path.split(full_path)
	
	if not os.path.exists(full_path):
		print("Couldn't find the file, wrong path: " + file_name)
		return False
	
	if full_path[-6:] != ".bfstp":
		print("Wrong file extension: " + file_name)
		return False
		
	file = open(full_path, "rb")
	data = bytearray(file.read()) # read tha bytes
	file.close()
	
	magic = data[:4]
	if magic != b"FSTP":
		print("Not a valid FSTP signature: " + file_name)
		return False
		
	bom = '>' if data[4:6] == b"\xFE\xFF" else '<' # get the file bom
	info_offset, info_size = struct.unpack(bom + "2I", data[24:32])
	data_flag = struct.unpack(bom + "H", data[32:34])[0]
	if data_flag != 16385: # the freshly converted file has a SEEK section flag (0x4001), if it's not here then it means the file is already fixed or broken 
		print("This is a fixed bfstp, fixing not needed: " + file_name)
		return False
	
	seek_offset, seek_size = struct.unpack(bom + "2I", data[36:44])
	
	num_channels = data[info_offset+34]
	
	del data[seek_offset:seek_offset+seek_size] # remove the seek section
	
	pdat_offset = seek_offset
	pdat_len_per_channel = 24576 # the usual length of data per channel
	pdat_len = num_channels * pdat_len_per_channel # calc the usual PDAT's data length
	
	data[pdat_offset+4:pdat_offset+8] = struct.pack(bom + "I", pdat_len + 32) # full PDAT section length
	data[pdat_offset+16:pdat_offset+20] = struct.pack(bom + "I", pdat_len) # only data in PDAT length
	# just before the data in PDAT starts - usually stands 0x14 for WiiU (or Big Endian) and 0x54 for Switch (or Little Endian), currently assuming it's about BOM
	data[pdat_offset+28:pdat_offset+32] = struct.pack(bom + "I", 0x14 if bom == ">" else 0x34) 
	del data[pdat_offset+32+pdat_len:] # trim all the unnecessary data
	
	data[32:34] = struct.pack(bom + "H", 16388) # write the PDAT section flag - 0x4004
	data[36:44] = struct.pack(bom + "2I", pdat_offset, pdat_len + 32) # write the offset to the PDAT section and it's whole length
	data[44:64] = [0]*20 # fill the rest of the FSTP section with 0
	
	data[12:16] = struct.pack(bom + "I", len(data)) # write the whole file size here
	
	file = open(full_path[:-6]+"_fixed.bfstp", "wb")
	file.write(data)
	file.close()
	return True

if __name__ == '__main__':
	len_arg = len(sys.argv)
	
	any_error = False
	
	if len_arg == 1:
		print("Usage: Please specify the input file(s) as argument(s)")
		any_error = True
	else:
		for x in range(1, len_arg):
			if not fix(sys.argv[x]):
				any_error = True
	
	if any_error:
		time.sleep(3)