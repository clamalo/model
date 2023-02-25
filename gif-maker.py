with open('model_config.txt', 'r') as myfile:
    text=myfile.read()
    text = text.split('\n')
    for arg in range(len(text)):
        config = text[arg].split('=')[1]
        config = config.replace(' ','')
        text[arg] = config
    directory = text[0]

import imageio

step = int(input('Step: '))
start_frame = int(input('Start frame: '))
end_frame = int(input('End frame: '))
parameter = input('Parameter: ')

images = []
for frame_number in range(start_frame,end_frame+1,step):
    images.append(imageio.imread(directory+'outputs/figures/'+parameter+'/'+parameter+'_'+str(frame_number)+'.png'))
imageio.mimsave(directory+'outputs/custom.gif', images, duration=0.2)
