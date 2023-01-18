from datetime import datetime
import sys
date = sys.argv[1]


date_obj = datetime.strptime(date,"%Y%m%d")
date_str = date_obj.strftime("%Y%j")
print(date_str)


