# MAPPING ONLY

BÀI THỰC HÀNH HỌC MÁY

LAB 1a – Công cụ và Thư viện ML
Mục tiêu
• Cài đặt và làm quen môi trường Python cho ML
• Thành thạo các thao tác cơ bản với Numpy, Pandas
• Trực quan hóa dữ liệu với Matplotlib
• Load và khám phá dữ liệu mẫu
Công cụ
• Môi trường: Google Colab / Jupyter Notebook
• Thư viện: Numpy, Pandas, Matplotlib, Scikit-learn
Quy trình
• Phần A: Setup môi trường
o Sử dụng Google Colab
o Tạo notebook mới, import các thư viện
• Phần B: Numpy cơ bản
o Tạo arrays, reshape, indexing, slicing
o Dot product, broadcasting, Random, statistics functions
• Phần C: Pandas cơ bản
o Load CSV/Excel: pd.read_csv()
o Khám phá: head(), info(), describe()
o Filtering, groupby, handling missing values
• Phần D: Matplotlib cơ bản
o Line plot, Scatter plot
o Subplots, labels, legends, titles
• Phần E: Load dữ liệu mẫu
o Load dataset từ sklearn (iris, boston, digits)
o EDA cơ bản trên dữ liệu mẫu

Output
• Ít nhất 3 loại biểu đồ khác nhau
• Summary statistics của dữ liệu mẫu

LAB 1b – Machine Learning Project (End-to-End)
Mục tiêu
• Nắm và hiểu rõ quy trình một dự án ML từ đầu đến cuối
• Thực hành từ Raw Data đến file model.pkl
• Áp dụng đầy đủ các bước: EDA → Preprocessing → Training → Tuning
→ Evaluation
Dữ liệu
• Dữ liệu thô (Excel/CSV)
• Dưới 10 thuộc tính, trên 1000 samples
• Gợi ý: House Prices, Titanic, Customer Churn, hoặc tự chọn
Quy trình
• Bước 1: Thu thập Dữ liệu
• Bước 2: Khám phá và Trực quan hóa (EDA)
• Bước 3: Chuẩn bị Dữ liệu
• Bước 4: Chọn và Huấn luyện Mô hình
• Bước 5: Tinh chỉnh Mô hình
• Bước 6: Lưu Model
Output
• Screenshot: Code + Kết quả thống kê, trực quan hóa song song
• Các biểu đồ EDA + Kết quả huấn luyện

LAB 2a – Dimensionality Reduction (PCA, Kernel PCA)
Mục tiêu
• Hiểu và cài đặt PCA thủ công bằng Numpy/SVD
• So sánh với PCA của Scikit-Learn
• Trực quan hóa dữ liệu trước/sau giảm chiều
• Thực hành Kernel PCA với dữ liệu phi tuyến
Dữ liệu
• Dataset có nhiều chiều (≥5features, ≥500 samples)
• Gợi ý: Iris, Wine, hoặc MNIST subset

Quy trình
• Bước 1: Chuẩn bị dữ liệu
• Bước 2: PCA thủ công (Numpy)
• Bước 3: So sánh PCA với Scikit-Learn
• Bước 4: Trực quan hóa
• Bước 5: Kernel PCA
Output
• Code + Kết quả trực quan hóa song song
• Bảng so sánh: PCA thủ công vs Sklearn
• Scree plot +2D projection plots

LAB 2b – Dimensionality Reduction (t-SNE, UMAP, LLE)
Mục tiêu
• Trực quan hóa dữ liệu cao chiều bằng t-SNE và UMAP
• So sánh sự phân tách cụm giữa PCA vs t-SNE vs UMAP
• Hiểu ảnh hưởng của hyperparameters (perplexity, n_neighbors)
• Nhận biết khi nào dùng phương pháp nào
Dữ liệu
• MNIST hoặc Fashion-MNIST (subset ~5000 samples)
• 784 chiều → 2D để trực quan hóa
Quy trình
• Bước 1: Load và chuẩn bị dữ liệu (sampling, normalize)
• Bước 2: Giảm chiều bằng PCA →2D
• Bước 3: Giảm chiều bằng t-SNE → 2D (thử nhiều perplexity)
• Bước 4: Giảm chiều bằng UMAP → 2D
• Bước 5: So sánh trực quan 3phương pháp
Output
• 3 scatter plots cạnh nhau: PCA vs t-SNE vs UMAP
• Bảng so sánh: Thời gian chạy, độ phân tách cụm

LAB 3a – Regression Techniques (Gradient Descent, Linear
Regression)
Mục tiêu
• Hiểu và cài đặt Gradient Descent từ đầu (Batch GD)
• So sánh tốc độ hội tụ với các learning rate khác nhau
• Cài đặt Linear Regression bằng Normal Equation và GD
• So sánh hai phương pháp: Normal Equation vs Gradient Descent
Dữ liệu
• Dữ liệu tuyến tính đơn giản (tự tạo hoặc dataset có sẵn)
• Gợi ý: Boston Housing, California Housing, hoặc synthetic data
Quy trình
• Bước 1: Tạo/Load dữ liệu, trực quan hóa
• Bước 2: Cài đặt Gradient Descent thủ công (Numpy)
• Bước 3: Thử nghiệm với nhiều learning rates (0.001, 0.01, 0.1, 1.0)
• Bước 4: Cài đặt Normal Equation, so sánh kết quả
• Bước 5: So sánh với sklearn.linear_model.LinearRegression
Output
• Đồ thị Loss vs Iterations với các learning rates khác nhau
• Bảng so sánh: Thời gian chạy, MSE cuối cùng
• Đồ thị đường hồi quy (regression line) trên dữ liệu

LAB 3b – Regression Techniques (Polynomial Regression, Logistic
Regression)
Mục tiêu
• Hiểu Polynomial Regression và Bias-Variance Tradeoff
• Vẽ Learning Curves để chẩn đoán Under/Overfitting
• Cài đặt Logistic Regression thủ công cho bài toán phân loại
• Hiểu Sigmoid, Decision Boundary, và Log Loss
Dữ liệu
• Polynomial: Dữ liệu phi tuyến (tự tạo hoặc có sẵn)

• Logistic: Churn Prediction hoặc Iris Dataset
Quy trình
• Phần A: Polynomial Regression
o Bước 1: Tạo dữ liệu phi tuyến, fit Linear → thấy underfitting
o Bước 2: Thử các bậc đa thức (degree = 1, 2, 4, 10, 15)
o Bước 3: Vẽ Learning Curves, nhận diện under/overfitting
• Phần B: Logistic Regression
o Bước 4: Load dữ liệu Churn/Iris, EDA cơ bản
o Bước 5: Sử dụng Gradient Descent đã code ở lab khác và code Logistic
Regression thủ công (numpy)
o Bước 6: Vẽ Decision Boundary (2D)
o Bước 7: Đánh giá: Accuracy, Confusion Matrix

Output
• Đồ thị so sánh các bậc đa thức (under/over/good fit)
• Learning Curves cho2-3 mô hình
• Decision Boundary plot + Confusion Matrix

LAB 4a: Classification Techniques (KNN)
Mục tiêu
• Hiểu và triển khai K-Nearest Neighbors thủ công
• Quan sát ảnh hưởng của K đến Decision Boundary
• So sánh KNN vs K khác nhau
Dữ liệu
• KNN: Iris hoặc synthetic2D data (để vẽ boundary)
Quy trình
• Bước 1: Load dữ liệu 2D, trực quan hóa
• Bước 2: Code và train KNN thủ công với K = 1, 5, 15, 50
• Bước 3: Vẽ Decision Boundary cho từng K
• Bước 4: Nhận xét under/overfitting theo K
Output
• Decision Boundary plots với các giá trị K khác nhau

• Bảng so sánh: KNN với các K khác nhau

LAB 4b: Classification Techniques (Decision Tree)
Mục tiêu
• Cài đặt Decision Tree thủ công bằng Numpy (không dùng sklearn)
• Hiểu thuật toán CART và tiêu chuẩn Gini/Entropy
• Visualize cây quyết định
• Thử nghiệm regularization (max_depth, min_samples)
Dữ liệu
• Healthcare dataset (Heart Disease, Diabetes, hoặc tương tự)
• Số features vừa phải để visualize được cây
Quy trình
• Bước 1: Load dữ liệu, EDA cơ bản
• Bước 2: Cài đặt hàm tính Gini Impurity
• Bước 3: Cài đặt hàm tìm best split (greedy search)
• Bước 4: Xây dựng cây đệ quy (recursive splitting)
• Bước 5: Cài đặt hàm predict
• Bước 6: So sánh kết quả với sklearn DecisionTreeClassifier
• Bước 7: Visualize cây (text-based hoặc graphviz)
Output
• Code Decision Tree thủ công hoàn chỉnh
• Visualize cây quyết định (ít nhất dạng text)
• Bảng so sánh: Accuracy thủ công vs sklearn

Lab 4c: Classification Techniques (SVM)
Mục tiêu
• Hiểu ý tưởng Maximum Margin và Support Vectors
• Phân biệt Hard Margin vs Soft Margin
• Áp dụng Kernel Trick cho dữ liệu phi tuyến
• Thử nghiệm hyperparameters C và gamma

Dữ liệu
• Synthetic: make_moons, make_circles (phi tuyến)
• Dữ liệu2D để visualize Decision Boundary
Quy trình
• Bước 1: Tạo dữ liệu make_moons, trực quan hóa
• Bước 2: Thử Linear SVM → thấy thất bại
• Bước 3: Áp dụng SVM với RBF Kernel (code thủ công)
• Bước 4: Thử nghiệm C = 0.1,1, 10, 100 → vẽ boundary
• Bước 5: Thử nghiệm gamma = 0.1, 1, 10 → vẽ boundary
• Bước 6: Visualize Support Vectors
Output
• Decision Boundary: Linear vs RBF Kernel
• Grid plots:Ảnh hưởng của C và gamma
• Highlight Support Vectors trên đồ thị

Lab 4d: Model Evaluation (Metrics & Imbalanced Data)
Mục tiêu
• Hiểu vấn đề của Accuracy vớidữ liệu mất cân bằng
• Sử dụng thành thạo Confusion Matrix, Precision, Recall, F1
• Vẽ và diễn giải ROC Curve, tính AUC
• So sánh các metrics trên cùng bài toán
Dữ liệu
• Imbalanced dataset: Credit Card Fraud, hoặc tự tạo (90% negative, 10%
positive)
• Bài toán binary classification
Quy trình
• Bước 1: Load dữ liệu, kiểm tra tỷ lệ class imbalance
• Bước 2: Train baseline model (Logistic Regression hoặc bất kỳ) (có thể
dùng thư viện)
• Bước 3: Tính Accuracy → thấy cao nhưng vô nghĩa
• Bước 4: Vẽ Confusion Matrix (matplotlib/seaborn heatmap)

• Bước 5: Tính Precision, Recall, F1-Score
• Bước 6: Vẽ ROC Curve, tính AUC
• Bước 7: Thử các threshold khác nhau → quan sát trade-off
Output
• Confusion Matrix heatmap
• Bảng: Accuracy, Precision, Recall, F1, AUC
• ROC Curve với AUC score

Lab 5: Ensemble Learning (Bagging, Random Forests, Boosting)
Mục tiêu
• Hiểu và áp dụng Voting Classifier (Hard/Soft)
• So sánh Bagging vs Pasting
• Sử dụng Random Forest và trích xuất Feature Importance
• Áp dụng XGBoost/LightGBM để tối ưu accuracy
Dữ liệu
• Tabular dataset: Titanic, Heart Disease, hoặc tương tự
• Đủ features để thấy được Feature Importance
Quy trình
• Bước 1: Train các base models riêng lẻ (Logistic, SVM, Tree) (có thể
dùng thư viện)
• Bước 2: Voting Classifier (Hard + Soft), so sánh với base models
• Bước 3: Bagging Classifier, sử dụng OOB Score
• Bước 4: Random Forest, visualize Feature Importance
• Bước 5: Gradient Boosting / XGBoost
• Bước 6: So sánh tất cả phương pháp
Output
• Bảng so sánh Accuracy: Base models vs Voting vs Bagging vs RF vs
XGBoost
• Bar chart: Feature Importance từ Random Forest

Lab 6a: Clustering Techniques (K-Means, Mean Shift, DBSCAN)
Mục tiêu
• Cài đặt K-Means thủ công bằng Numpy
• Áp dụng Customer Segmentation thực tế
• So sánh K-Means vs DBSCAN trên dữ liệu hình dạng khác nhau
• Sử dụng Elbow Method và Silhouette Score để chọn K
Dữ liệu
• Customer Segmentation: Mall Customers hoặc tương tự
• Synthetic: make_moons, make_circles (để so sánh với DBSCAN)
Quy trình
• Phần A: K-Means thủ công
o Bước 1: Cài đặt K-Means từ đầu (random init → assign → update)
o Bước 2: Cài đặt K-Means++ initialization
o Bước 3: Elbow Method → chọn K tối ưu
o Bước 4: Tính Silhouette Score
• Phần B: Customer Segmentation
o Bước 5: Load Mall Customers, EDA
o Bước 6: Áp dụng K-Means, visualize clusters
• Phần C: So sánh với DBSCAN
o Bước 7: Tạo make_moons, thử K-Means → thất bại
o Bước 8: Áp dụng DBSCAN → thành công

Output
• Code K-Means thủ công hoàn chỉnh
• Elbow plot + Silhouette plot
• Scatter plots: K-Means vs DBSCAN trên dữ liệu hình dạng lạ

Lab 6b: Clustering Techniques (Gaussian Mixture Models -
GMM)
Mục tiêu
• Hiểu GMM như soft clustering (so với K-Means hard clustering)
• Hiểu thuật toán EM (Expectation-Maximization)

• Áp dụng GMM cho Anomaly Detection
• Xây dựng hệ thống phát hiện bất thường thực tế
Dữ liệu
• Network Intrusion: KDD Cup 99 (subset) hoặc NSL-KDD
• Hoặc: Manufacturing defect dataset
Quy trình
• Bước 1: Load dữ liệu, EDA, preprocessing
• Bước 2: Train GMM trên dữ liệu "bình thường" (Thủ công)
• Bước 3: Tính log-likelihood cho mỗi điểm
• Bước 4: Xác định threshold (percentile hoặc validation)
• Bước 5: Đánh dấu điểm có p(x) < threshold là Anomaly
• Bước 6: Đánh giá: Precision, Recall, F1 (nếu có nhãn)
• Bước 7: So sánh GMM vs K-Means clustering
Output
• Scatter plot: Normal vs Anomaly points
• Distribution plot của log-likelihood scores
• Confusion Matrix (nếu có ground truth)
• Bảng so sánh: GMM vs K-Means trên cùng dữ liệu