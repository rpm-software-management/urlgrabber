from munittest import *

base_http = 'http://www.linux.duke.edu/projects/urlgrabber/test/'

reference_data = ''.join( [str(i)+'\n' for i in range(20000) ] )
ref_http = base_http + 'reference'
short_reference_data = ' '.join( [str(i) for i in range(10) ] )
short_ref_http = base_http + 'short_reference'

ref_200 = ref_http
ref_404 = base_http + 'nonexistent_file'
ref_403 = base_http + 'mirror/broken/'

base_mirror_url    = base_http + 'mirror/'
good_mirrors       = ['m1', 'm2', 'm3']
mirror_files       = ['test1.txt', 'test2.txt']
bad_mirrors        = ['broken']
bad_mirror_files   = ['broken.txt']
