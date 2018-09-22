# Ec2StartStopBytag
#
Script d'arret/relance d'instance ec2 Amazon.

Le script récupére l'état des instances (Running/Stopped), et pour chacune d'elle va lire ses tags pour récupérer ses heures
de démarrage et d'arrêt (StartDailyTime/StopDailyTime) et ses jours de fonctionnement (OpeningDays).
En fonction des tags le script va démarrer ou arrêter l'instance.
