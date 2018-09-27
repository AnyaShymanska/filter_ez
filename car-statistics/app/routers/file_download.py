import json

from app import app, logger
from app.models import Dataset, File
from app.services import utils, notify_admin, send_result_to_mail
from flask import send_file, session
from flask_login import login_required


@app.route("/api/download/<int:dataset_id>", methods=['GET'])
@login_required
def download(dataset_id):
    """
    Returns xls file. If dataset.filter_id is equal to None, returns original file
    else read DataFrame from it and removes all rows which are in dataset.included_rows
    and then writes changed DataFrame to ByteIO object which is sent as a file
    :param dataset_id: id of dataset to return for download
    :return: File or JSON with error
    """
    user_id = int(session.get('user_id', 0))
    dataset = Dataset.query.filter(Dataset.id == int(dataset_id)).first()

    if not dataset:
        return json.dumps({'message': 'file does not exist'}), 404

    if dataset.user_id != user_id:
        return json.dumps({'message': 'access forbidden'}), 403

    if dataset.filter_id:
        file_data = utils.dataset_to_excel(dataset)  # Creates BytesIO objects with dataset
        if file_data:
            logger.info(f"User {user_id} successfully downloaded dataset {dataset_id}")
            return send_file(file_data,
                             attachment_filename='result.xlsx',
                             as_attachment=True,
                             mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        else:
            logger.error(f"error when user {user_id} downloaded {dataset_id}")
            notify_admin(error_level="ERROR",
                         message=f"Unexpected error occurred when user {user_id} tried to download"
                                 f" dataset {dataset_id}")
            return json.dumps({'message': 'couldn\'t send file to user'}), 500
    else:
        return send_file(utils.get_file_path(dataset.file_id))


@app.route('/test')
def test():
    dataset = Dataset.query.all()[-1]
    print(utils.get_user_file(dataset.file_id, dataset.user_id))
    send_result_to_mail(['sturss22@gmail.com'],
                        'result.xls',
                        open(utils.get_user_file(dataset.file_id, dataset.user_id), 'rb').read())
    return json.dumps({'data': 'Email has been sent'})
