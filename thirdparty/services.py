# import threading

# # from thirdparty.FocusAPI import getFocusData  

# thread = None  

# class FocusDataSyncThread(threading.Thread):
#     def __init__(self, **args):
#         self.args = args
#         threading.Thread.__init__(self)
#     def run(self):
#         # getFocusData()

# def start_focus_data_sync(**args):
#     global thread
#     thread = FocusDataSyncThread(**args)
#     thread.start()
#     # thread.run()  # Pass the variable to the class method
    

# def is_focus_data_syncing():
#     global thread
#     if thread is not None:
#         print('Thread is running:', thread.is_alive())
#         return thread.is_alive()
#     else:
#         print('thread is None:',)
#         return False
    


