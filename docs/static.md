# MVC Architecture

The architecture of the lab assistant software follows a MVC (Model-View-Controller) architecture where the events triggered by the user are (mostly) processed by the controller that, in turn, updates the views and models. As a consequence, the application logic is implemented by the controller.  

To avoid spaghettification and enforce clarity of the code, the definitions of the classes follow a strict hierarchy with the controller on the top, below the views, at the bottom the models.  

As a visualization of the software architecture and its class hierarchy the classes and some of the classless modules are presented in the following UML class diagram.

**UML class diagram**
![classes](docs/classes.png)