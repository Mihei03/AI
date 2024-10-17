import tensorflow as tf
from tensorflow.python.client import device_lib

print(tf.test.is_built_with_cuda())
#print(tf.test.is_built_with_cudnn()) #command not working from tensorflow 2.0

#print(tf.sysconfig.get_build_info(), "\n") #static numbers
sys_details = tf.sysconfig.get_build_info()
#print('Prescribed CUDA version:', sys_details["cuda_version"]) #static number, no depend on actual version
#print('Prescribed cuDNN version:', sys_details["cudnn_version"], "\n") #static number no depend on actual version
print('Is CUDA build:', sys_details["is_cuda_build"])
print(tf.reduce_sum(tf.random.normal([1000, 1000]))) #official recommendation to check CPU is enabled
print(tf.config.list_physical_devices('GPU'), "\n") #official recommendation to check GPU is enabled

print(device_lib.list_local_devices())