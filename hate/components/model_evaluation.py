import os
import sys
import keras
import pickle
import numpy as np
import pandas as pd
from hate.logger import logging
from hate.exception import CustomException
from keras.utils import pad_sequences
from hate.constants import *
# from hate.ml.model import ModelArchitecture
from hate.configuration.gcloud_syncer import GCloudSync
# from keras.preprocessing.text import Tokenizer
from sklearn.metrics import confusion_matrix
from hate.entity.config_entity import ModelEvaluationConfig
from hate.entity.artifact_entity import ModelEvaluationArtifacts, ModelTrainerArtifacts, DataTransformationArtifacts


class ModelEvaluation:
    def __init__(self, model_evaluation_config: ModelEvaluationConfig,
                 model_trainer_artifacts: ModelTrainerArtifacts,
                 data_transformation_artifacts: DataTransformationArtifacts):
        """
        :param model_evaluation_config: Configuration for model eva            model = model_architecture.get_model()
 data transformation artifact stage
        :param model_trainer_artifacts: Output reference of model trainer artifact stage
        """

        self.model_evaluation_config = model_evaluation_config
        self.model_trainer_artifacts = model_trainer_artifacts
        self.data_transformation_artifacts = data_transformation_artifacts
        self.gcloud = GCloudSync()


    
    def get_best_model_from_gcloud(self) -> str:
        """
        :return: Fetch best model from gcloud storage and store inside best model directory path
        """
        try:
            logging.info("Entered the get_best_model_from_gcloud method of Model Evaluation class")

            os.makedirs(self.model_evaluation_config.BEST_MODEL_DIR_PATH, exist_ok=True)

            self.gcloud.sync_folder_from_gcloud(self.model_evaluation_config.BUCKET_NAME,
                                                self.model_evaluation_config.MODEL_NAME,
                                                self.model_evaluation_config.BEST_MODEL_DIR_PATH)

            best_model_path = os.path.join(self.model_evaluation_config.BEST_MODEL_DIR_PATH,
                                           self.model_evaluation_config.MODEL_NAME)
            logging.info("Exited the get_best_model_from_gcloud method of Model Evaluation class")
            return best_model_path
        except Exception as e:
            raise CustomException(e, sys) from e 
        

    
    def evaluate(self):
        """

        :param model: Currently trained model or best model from gcloud storage
        :param data_loader: Data loader for validation dataset
        :return: loss
        """
        try:
            logging.info("Entering into to the evaluate function of Model Evaluation class")
            print(self.model_trainer_artifacts.x_test_path)

            x_test = pd.read_csv(self.model_trainer_artifacts.x_test_path,index_col=0)
            print(x_test)
            y_test = pd.read_csv(self.model_trainer_artifacts.y_test_path,index_col=0)

            with open('tokenizer.pickle', 'rb') as handle:
                tokenizer = pickle.load(handle)

            load_model=keras.models.load_model(self.model_trainer_artifacts.trained_model_path)

            x_test = x_test['tweet'].astype(str)

            x_test = x_test.squeeze()
            y_test = y_test.squeeze()

            test_sequences = tokenizer.texts_to_sequences(x_test)
            test_sequences_matrix = pad_sequences(test_sequences,maxlen=MAX_LEN)
            print(f"----------{test_sequences_matrix}------------------")

            print(f"-----------------{x_test.shape}--------------")
            print(f"-----------------{y_test.shape}--------------")
            accuracy = load_model.evaluate(test_sequences_matrix,y_test)
            logging.info(f"the test accuracy is {accuracy}")

            lstm_prediction = load_model.predict(test_sequences_matrix)
            res = []
            for prediction in lstm_prediction:
                if prediction[0] < 0.5:
                    res.append(0)
                else:
                    res.append(1)
            print(confusion_matrix(y_test,res))
            logging.info(f"the confusion_matrix is {confusion_matrix(y_test,res)} ")
            return accuracy
        except Exception as e:
            raise CustomException(e, sys) from e
        

    
    def initiate_model_evaluation(self) -> ModelEvaluationArtifacts:
        """
            Method Name :   initiate_model_evaluation
            Description :   This function is used to initiate all steps of the model evaluation

            Output      :   Returns model evaluation artifact
            On Failure  :   Write an exception log and then raise an exception
        """
        logging.info("Initiate Model Evaluation")
        try:

            logging.info("Loading currently trained model")
            trained_model=keras.models.load_model(self.model_trainer_artifacts.trained_model_path)
            with open('tokenizer.pickle', 'rb') as handle:
                load_tokenizer = pickle.load(handle)

            trained_model_accuracy = self.evaluate()

            logging.info("Fetch best model from gcloud storage")
            best_model_path = self.get_best_model_from_gcloud()

            logging.info("Check is best model present in the gcloud storage or not ?")
            if os.path.isfile(best_model_path) is False:
                is_model_accepted = True
                logging.info("glcoud storage model is false and currently trained model accepted is true")

            else:
                logging.info("Load best model fetched from gcloud storage")
                best_model=keras.models.load_model(best_model_path)
                best_model_accuracy= self.evaluate()

                logging.info("Comparing loss between best_model_loss and trained_model_loss ? ")
                if best_model_accuracy > trained_model_accuracy:
                    is_model_accepted = True
                    logging.info("Trained model not accepted")
                else:
                    is_model_accepted = False
                    logging.info("Trained model accepted")

            model_evaluation_artifacts = ModelEvaluationArtifacts(is_model_accepted=is_model_accepted)
            logging.info("Returning the ModelEvaluationArtifacts")
            return model_evaluation_artifacts

        except Exception as e:
            raise CustomException(e, sys) from e



