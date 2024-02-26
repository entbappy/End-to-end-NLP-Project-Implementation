import sys
from hate.logger import logging
from hate.exception import CustomException
from hate.components.data_ingestion import DataIngestion
from hate.components.data_transforamation import DataTransformation
from hate.components.model_trainer import ModelTrainer
from hate.components.model_evaluation import ModelEvaluation
from hate.components.model_pusher import ModelPusher

from hate.entity.config_entity import (DataIngestionConfig,
                                       DataTransformationConfig,
                                       ModelTrainerConfig,
                                       ModelEvaluationConfig,
                                       ModelPusherConfig)

from hate.entity.artifact_entity import (DataIngestionArtifacts,
                                         DataTransformationArtifacts,
                                         ModelTrainerArtifacts,
                                         ModelEvaluationArtifacts,
                                         ModelPusherArtifacts)


class TrainPipeline:
    def __init__(self):
        self.data_ingestion_config = DataIngestionConfig()
        self.data_transformation_config = DataTransformationConfig()
        self.model_trainer_config = ModelTrainerConfig()
        self.model_evaluation_config =ModelEvaluationConfig()
        self.model_pusher_config = ModelPusherConfig()


    

    def start_data_ingestion(self) -> DataIngestionArtifacts:
        logging.info("Entered the start_data_ingestion method of TrainPipeline class")
        try:
            logging.info("Getting the data from GCLoud Storage bucket")
            data_ingestion = DataIngestion(data_ingestion_config = self.data_ingestion_config)

            data_ingestion_artifacts = data_ingestion.initiate_data_ingestion()
            logging.info("Got the train and valid from GCLoud Storage")
            logging.info("Exited the start_data_ingestion method of TrainPipeline class")
            return data_ingestion_artifacts

        except Exception as e:
            raise CustomException(e, sys) from e
        
    

    def start_data_transformation(self, data_ingestion_artifacts = DataIngestionArtifacts) -> DataTransformationArtifacts:
        logging.info("Entered the start_data_transformation method of TrainPipeline class")
        try:
            data_transformation = DataTransformation(
                data_ingestion_artifacts = data_ingestion_artifacts,
                data_transformation_config=self.data_transformation_config
            )

            data_transformation_artifacts = data_transformation.initiate_data_transformation()
            
            logging.info("Exited the start_data_transformation method of TrainPipeline class")
            return data_transformation_artifacts

        except Exception as e:
            raise CustomException(e, sys) from e
        

    
    def start_model_trainer(self, data_transformation_artifacts: DataTransformationArtifacts) -> ModelTrainerArtifacts:
        logging.info(
            "Entered the start_model_trainer method of TrainPipeline class"
        )
        try:
            model_trainer = ModelTrainer(data_transformation_artifacts=data_transformation_artifacts,
                                        model_trainer_config=self.model_trainer_config
                                        )
            model_trainer_artifacts = model_trainer.initiate_model_trainer()
            logging.info("Exited the start_model_trainer method of TrainPipeline class")
            return model_trainer_artifacts

        except Exception as e:
            raise CustomException(e, sys) 
        

    
    def start_model_evaluation(self, model_trainer_artifacts: ModelTrainerArtifacts, data_transformation_artifacts: DataTransformationArtifacts) -> ModelEvaluationArtifacts:
        logging.info("Entered the start_model_evaluation method of TrainPipeline class")
        try:
            model_evaluation = ModelEvaluation(data_transformation_artifacts = data_transformation_artifacts,
                                                model_evaluation_config=self.model_evaluation_config,
                                                model_trainer_artifacts=model_trainer_artifacts)

            model_evaluation_artifacts = model_evaluation.initiate_model_evaluation()
            logging.info("Exited the start_model_evaluation method of TrainPipeline class")
            return model_evaluation_artifacts

        except Exception as e:
            raise CustomException(e, sys) from e
        
    

    def start_model_pusher(self,) -> ModelPusherArtifacts:
        logging.info("Entered the start_model_pusher method of TrainPipeline class")
        try:
            model_pusher = ModelPusher(
                model_pusher_config=self.model_pusher_config,
            )
            model_pusher_artifact = model_pusher.initiate_model_pusher()
            logging.info("Initiated the model pusher")
            logging.info("Exited the start_model_pusher method of TrainPipeline class")
            return model_pusher_artifact

        except Exception as e:
            raise CustomException(e, sys) from e

        
    

    def run_pipeline(self):
        logging.info("Entered the run_pipeline method of TrainPipeline class")
        try:
            data_ingestion_artifacts = self.start_data_ingestion()

            data_transformation_artifacts = self.start_data_transformation(
                data_ingestion_artifacts=data_ingestion_artifacts
            )

            model_trainer_artifacts = self.start_model_trainer(
                data_transformation_artifacts=data_transformation_artifacts
            )

            model_evaluation_artifacts = self.start_model_evaluation(model_trainer_artifacts=model_trainer_artifacts,
                                                                    data_transformation_artifacts=data_transformation_artifacts
            ) 

            if not model_evaluation_artifacts.is_model_accepted:
                raise Exception("Trained model is not better than the best model")
            
            model_pusher_artifacts = self.start_model_pusher()





            logging.info("Exited the run_pipeline method of TrainPipeline class") 

        except Exception as e:
            raise CustomException(e, sys) from e
