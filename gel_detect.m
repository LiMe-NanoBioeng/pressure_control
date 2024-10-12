x_tiles = 1;
y_tiles = 1;


directory = "/home/samba/public/nozaki/data/20241009/NC_t1_1/";

for x = 0: x_tiles - 1
    for y = 0: y_tiles - 1
filename = sprintf("NC_t1_MMStack_1-Pos%03d_%03d.ome.tif", x, y);

file_path = strcat(directory,filename);

   
    img = imread(file_path, 1);
   
   
    imshow(img, []);  
    %BW = imbinarize(img, 0.0058);
    
    [centers, radii, metric] = imfindcircles(img,[65 150], "EdgeThreshold",0.01, Sensitivity=0.96);
    
   
  
    
  
subplot(x_tiles, y_tiles, x+y+2);  % 
imshow(img, []);
viscircles(centers, radii,'EdgeColor','b');
title('Img');  % 
%subplot(1, 2, 2);  % 
%title('BW');  % 
%imshow(BW,[]);
    end
end
    
    
    %end
