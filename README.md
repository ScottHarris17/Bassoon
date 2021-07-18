# Bassoon
Develop, organize, and deploy vision science experiments. Bassoon is a lightweight, python based GUI and API to easily manage and deploy visual stimuli. While the stimuli included with this project rely on <a href = 'www.psychopy.org'>Psychopy</a>, any backend stimulus framework can in theory be used with local copies of Bassoon.

<h2> Installation </h2>
As currently packaged, Bassoon relies on python 3 and the Psychopy libraries. It is possible to launch Bassoon by simply cloning the Github repository and running /Bassoon/src/main.py as long as main.py can see Psychopy on your local device. That said, other installation techniques are recommended for ease of use with developing custom stimuli.

<h3>Installing with Anaconda</h3>
The easiest way to make sure your machine has all the dependencies that are required to run Bassoon is to install Psychopy as an Anaconda environment.
First download and install <a href = 'https://www.anaconda.com/products/individual'>Anaconda</a> if you do not already have it. Make sure your installation is set to include python 3+.
Next, <a href = 'https://www.psychopy.org/download.html#conda'>install Psychopy as an Anaconda environment.</a> You'll want to download the .yml file provided by Psychopy. If you are having trouble finding it, a copy of this file is included in this repository at /Bassoon/help/psychopy (no guarantees this is up to date).
While it's not absolutely critical, it's also a good idea to have an IDE from which to launch, edit, and add to Bassoon. My preferred IDE is <a href = 'https://www.spyder-ide.org/'>Spyder,</a> but you can choose any. If you do choose Spyder, it is easy to install into your newly built Psychopy environment: launch the Anaconda Navigator app and select "environments" from the panel on the lefthand side. If you've successfully installed Psychopy as an Anaconda environment you should see it listed here. Click on it to load the environment. Next, find the panel for Spyder in the list of applications and click "install."

<h3>Running Bassoon Using Anaconda</h3>
To run Bassoon, first download it onto your local device. Then launch the Anaconda command line ('anaconda prompt'). Enter the command 'conda activate psychopy' and then 'CD' to /Bassoon/src in your file directory. Enter the command 'python main.py' to run Bassoon from the command line. Alternatively, you can view the Bassoon source files by entering the command 'spyder'. You can edit and/or run Bassoon from within Spyder (or your preferred IDE). The Bassoon GUI is launched by running the main.py file.

<br><br>
Bassoon is free to use and community development is encouraged. If used for published science, let us know and please consider including a reference so that others can find us.

