import sys
sys.path.insert(0, "libs")
import pdb;pdb.set_trace()
import tftpc
cli = tftpc.TFtpClient()
cli.connect("127.0.0.1")
cli.put(sys.argv[1], sys.argv[2])
