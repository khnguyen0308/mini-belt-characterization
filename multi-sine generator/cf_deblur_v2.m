%%  Signal Optimization using deblurL2p
% (c) Mess- und Sensortechnik, TU Chemnitz
% Author: Ahmed Yahia Kallel
% Check LICENSE file for more details

%% inputs
% Mx_t: matrix of time
% A, f, Phi: amplitude, frequency, phase
% in f_freqbins_map: harmonics index
% s,S
clf

% plot?
dont_plot = 1;

% Regularization parameter (Lambda): smaller => converges to local faster
lambda = 1e-20;

% Lp norm (2N): higher = faster to converge, to local
px = 128;

% k factor (slope)
kfactor = 10;


deblurL2p.phi = Phi;


% use GPU? (CUDA only)
if exist('GPU','var') && GPU == 1
    S = gpuArray(S);
    s = gpuArray(s);
    deblurL2p.methodname = 'deblurL2p (GPU)';
else 
    deblurL2p.methodname = 'deblurL2p (CPU)';
end

% make sum
S = A.*cos(2.*pi.*f.*Mx_t+deblurL2p.phi);
s = sum(S,1);



% History
deblurL2p.histcf = zeros(MAX_ITER,1);
deblurL2p.modes = zeros(MAX_ITER,1);
deblurL2p.histpong = zeros(MAX_ITER,1);
deblurL2p.bestcf = 32768;
deblurL2p.bestphi = 32768;

tic();

MODE = 0; %0=>sigmoid, 1=>
NUMBER_OF_ROUNDS =40;

      
binx = [];
pkx = [];

    pp=0;
stalledCounter = 0;
ax = 0;
iterma = 0;

for i=1:MAX_ITER
    
        
    if MODE == 0 
    
        S = A.*cos(2.*pi.*f.*Mx_t+deblurL2p.phi);
        s = sum(S,1);
    
        % sigmoid transform
        s1 = (1./(1+exp(-s.'*kfactor)) - 0.5) ;
    
    
         X = fft(s1);
         deblurL2p.phi = angle(X(f_freqbins_map));
     
     
      elseif MODE == 1
    
            % Gauss Newton
                q = px/2;
                func = @(ax,phix)sum(ax.*cos(2.*pi.*f'.*repmat(t,numel(A),1)+deblurL2p.phi));
                dS_dPhiq = @(ax,phix,x,t) -q.*ax.*x.^(q-1).*sin(2.*pi.*f.*t +deblurL2p.phi);
                p =  deblurL2p.phi;
                r = ones(numel(t),1)*1;
                S = A.*cos(2.*pi.*f.*Mx_t+deblurL2p.phi);
                s = sum(S,1);
                r = (s.^q).'; %' * (s.^q) / N;
                J = [dS_dPhiq(A,deblurL2p.phi,s,t)]';
                p = p - (pinv(J'*J  + ones(size(J,2))* lambda)) * J' * r;
                deblurL2p.phi = p;
    
    
    
    
    
      end
      
         S = A.*cos(2.*pi.*f.*Mx_t+ deblurL2p.phi );
         s = sum(S,1);
    
    % used to determine stagnation, but found out that just a counter is
    % sufficient
    %  ax = ax*0.95 +  abs(pp - peak2rms(s))*0.05;
    
    
     stalledCounter = stalledCounter + 1;
    
     if  stalledCounter >= 100%
         
%          ax = 1; %reset accelerometer
         MODE =  rem(MODE + 1,2); %toggle mode
    
    
        stalledCounter = 0;
%         iterma = 0;
        if MODE == 1
    
                NUMBER_OF_ROUNDS = NUMBER_OF_ROUNDS - 1;
            fprintf('End of Round %d, best cf: %2.3f\n',NUMBER_OF_ROUNDS+1,deblurL2p.bestcf);
            if NUMBER_OF_ROUNDS == 0 
                break;
            end
        end
        
     end
%     pp = peak2rms(s);
 

    
    deblurL2p.histcf(i) = peak2rms(s);
    deblurL2p.modes(i) = MODE;
    deblurL2p.histpong(i) = toc();
    
    
    if deblurL2p.bestcf > deblurL2p.histcf(i)
        deblurL2p.bestcf = deblurL2p.histcf(i);
        deblurL2p.bestphi = deblurL2p.phi;
%         fprintf('Round: %d, best cf: %2.4f\n',NUMBER_OF_ROUNDS,deblurL2p.bestcf);
    end
    
       
     if ~dont_plot
         subplot(211)
         plot(s1)
         title(peak2rms(s));
         subplot(212)
         plot(s);
         drawnow
     end
     
     
  
end
deblurL2p.cf = peak2rms(s);
deblurL2p.elapsed = toc();
      fprintf('End of Round %d, best cf: %2.3f\n',NUMBER_OF_ROUNDS+1,deblurL2p.bestcf);
   
