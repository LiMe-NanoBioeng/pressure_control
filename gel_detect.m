x_tiles = 5;
y_tiles = 5;

directory = "C:/Users/keiji/OneDrive - Kyoto University (1)/20241009/NC_t1_1/";
%directory = "/home/samba/public/nozaki/data/20241009/NC_t1_1/";

% スタック用の空配列を初期化
stack = [];

for y = 0: x_tiles - 1
    for x = 0: y_tiles - 1
        filename = sprintf("NC_t1_MMStack_1-Pos%03d_%03d.ome.tif", x, y);
        file_path = strcat(directory, filename);
        
        % 画像を読み込む
        try
            img = imread(file_path, 1);
        catch ME
            fprintf('画像の読み込みに失敗しました: %s\nエラーメッセージ: %s\n', file_path, ME.message);
            continue; % エラーが発生した場合はスキップして次の画像に進む
        end
        
        % 画像サイズを取得
        [height, width, ~] = size(img);
        % 右側67%および上側67%の境界を計算
        right_boundary = width * 0.33;
        top_boundary = height * 0.33;
        
        % 境界を描画するための座標
        rectangle_coords = [
            right_boundary, 0;              % 左上
            right_boundary, top_boundary;    % 左下
            width, top_boundary;             % 右下
            width, 0;                        % 右上
            right_boundary, 0                % 最初の点に戻す
        ];

        % 円の除外リストを作成
        valid_indices = [];
        for i = 1:size(centers, 1)
            center_x = centers(i, 1);
            center_y = centers(i, 2);
            radius = radii(i);
            
            % 円が領域内に完全に収まるかをチェック
            if (center_x - radius >= right_boundary) && (center_y - radius >= top_boundary) && ...
               (center_x + radius <= width) && (center_y + radius <= height)
                valid_indices = [valid_indices; i];
            end
        end
        
        % 有効な円のみをフィルタリング
        valid_centers = centers(valid_indices, :);
        valid_radii = radii(valid_indices);
        
        % 検出した円を元の画像に描画
        img_with_circles = insertShape(img, 'Circle', [valid_centers, valid_radii], 'Color', 'blue', 'LineWidth', 2);
        
        % 境界を画像に描画
        img_with_circles = insertShape(img_with_circles, 'Polygon', rectangle_coords, 'Color', 'red', 'LineWidth', 2);
        
        % 各円に番号を付けて描画
        for i = 1:size(valid_centers, 1)
            % 番号を付けるための位置（円の中心）を指定
            position = valid_centers(i, :);
            % 番号のテキストを指定
            label = sprintf('%d', i);
            % 番号を画像に描画
            img_with_circles = insertText(img_with_circles, position, label, 'FontSize', 18, 'TextColor', 'yellow', 'BoxOpacity', 0);
        end
        
        % 処理した画像をスタックに追加
        stack = cat(3, stack, img_with_circles);
        
        % 各画像をプロット
        subplot(x_tiles, y_tiles, x + 1 + 5 * y);
        imshow(img_with_circles, []);
        title('Detected Circles with Boundary');
    end
end

% スタックファイルを保存
output_filename = strcat(directory, "processed_stack_with_numbers_and_boundaries.tif");
imwrite(stack(:, :, 1), output_filename); % 最初の画像を保存

% その後の画像を追加
for i = 2:size(stack, 3)
    imwrite(stack(:, :, i), output_filename, 'WriteMode', 'append');
end

fprintf('スタックファイルが保存されました: %s\n', output_filename);

    %end
