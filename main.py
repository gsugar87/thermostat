import temp_monitor
import tweet_monitor
import database_monitor

# NEED THREADS FOR THESE!
temp_monitor.run()
tweet_monitor.run()
database_monitor.run()