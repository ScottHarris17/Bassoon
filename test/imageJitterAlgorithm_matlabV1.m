imageHeight = 1024;
imageWidth = 1024;

apertureDiameter_pix = 600;

%x, y - initialize at 0, 0 to start
currentX = 0;
currentY = 0;

positions = [0, 0];

meanSpeed = 0; %deg/s
stdSpeed = 40; %deg/s

frameRate = 60; %hz (1/s)

stimTime = 400;

framesPerStim = frameRate * stimTime;

pixPerDeg = 30;

meanSpeed_pix = meanSpeed*pixPerDeg / frameRate; %px/frame
stdSpeed_pix = stdSpeed*pixPerDeg / frameRate; %px/frame

meanComponents_pix = meanSpeed_pix/sqrt(2);
stdComponents_pix = stdSpeed_pix/sqrt(2);
adjustmentNeeded = 0;
adjustmentBegan = 0;

dxs = [];
for i = 1:framesPerStim
    if ~adjustmentNeeded
         
         dx = (randn(1)*stdComponents_pix);
         dy = (randn(1)*stdComponents_pix);
         positions(end+1, :) = [currentX, currentY] + [dx, dy];
            

         dxs = [dxs dx];

        currentX = positions(end, 1);
        currentY = positions(end, 2);
    
        if imageHeight - currentY < apertureDiameter_pix/2 || imageWidth - currentX < apertureDiameter_pix/2
            adjustmentNeeded = 1;
        end
    end

    if adjustmentNeeded
        if ~adjustmentBegan
            xyRatio = currentX/currentY;
            dy = meanSpeed_pix/sqrt(xyRatio^2 + 1);
            dx = xyRatio * dy;
            distancePerFrame = sqrt(dx^2 + dy^2);
            distanceToGo = sqrt(currentX^2 + currentY^2);
            framesToGo = round(distanceToGo/distancePerFrame); 
            adjustmentBegan = 1;
        end
        
        positions(end+1, :) = [currentX, currentY] - [dx, dy];

        currentX = positions(end, 1);
        currentY = positions(end, 2);

        framesToGo = framesToGo - 1;
        
        if framesToGo < 1
            adjustmentNeeded = 0;
            adjustmentBegan = 0;
        end
    end

end
positionsSmooth = movmean(positions, 10, 1);
figure
plot(positionsSmooth(:, 1), positionsSmooth(:, 2))


totalDxs = diff(positionsSmooth(:, 1));
totalDys = diff(positionsSmooth(:, 2));

speeds_pixPerFrame = sqrt(totalDxs.^2 + totalDys.^2);
speeds_degPerSec = speeds_pixPerFrame * frameRate / pixPerDeg;

figure
histogram(speeds_degPerSec)